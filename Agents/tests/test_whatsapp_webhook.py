"""
Tests for the WhatsApp webhook: Meta's verification handshake, signature
checking, payload parsing, and retry deduplication.
"""
import hashlib
import hmac
import json

import pytest

from whatsapp_webhook import (
    MessageDeduplicator,
    create_app,
    extract_messages,
    extract_statuses,
    split_profile_name,
    verify_signature,
)

APP_SECRET = "test-app-secret"
VERIFY_TOKEN = "test-verify-token"

INBOUND_TEXT = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WABA_ID",
        "changes": [{
            "field": "messages",
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "15550001111", "phone_number_id": "111222333"},
                "contacts": [{"profile": {"name": "Alice Smith"}, "wa_id": "15551234567"}],
                "messages": [{
                    "from": "15551234567",
                    "id": "wamid.ABC123",
                    "timestamp": "1717171717",
                    "type": "text",
                    "text": {"body": "/video"},
                }],
            },
        }],
    }],
}


def sign(body: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class RecordingDispatcher:
    """Captures dispatcher calls without running the agents."""

    def __init__(self):
        self.handled = []
        self.registered = []
        self.unsupported = []
        self.router = self

    async def mark_read(self, ref, message_id):
        return None

    def register_inbound(self, ref, profile=None):
        self.registered.append((ref, profile))

    async def handle_text(self, ref, text, profile=None):
        self.handled.append((ref, text, profile))
        return {"success": True}

    async def handle_unsupported(self, ref, message_type):
        self.unsupported.append((ref, message_type))
        return {"success": True}


class InlineWorker:
    """Runs submitted coroutines immediately so tests stay synchronous."""

    def __init__(self):
        self.submitted = 0

    def submit(self, coro):
        import asyncio

        self.submitted += 1
        asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def dispatcher():
    return RecordingDispatcher()


@pytest.fixture
def worker():
    return InlineWorker()


@pytest.fixture
def client(dispatcher, worker):
    app = create_app(dispatcher=dispatcher, worker=worker)
    app.config.update(TESTING=True)
    return app.test_client()


class TestVerificationHandshake:
    def test_echoes_challenge_when_token_matches(self, client):
        """Meta will not save the webhook unless hub.challenge is echoed verbatim."""
        response = client.get(
            "/webhook/whatsapp",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN,
                "hub.challenge": "1158201444",
            },
        )
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "1158201444"

    def test_rejects_wrong_token(self, client):
        response = client.get(
            "/webhook/whatsapp",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong",
                "hub.challenge": "123",
            },
        )
        assert response.status_code == 403

    def test_rejects_wrong_mode(self, client):
        response = client.get(
            "/webhook/whatsapp",
            query_string={
                "hub.mode": "unsubscribe",
                "hub.verify_token": VERIFY_TOKEN,
                "hub.challenge": "123",
            },
        )
        assert response.status_code == 403


class TestSignatureVerification:
    def test_accepts_a_correct_signature(self):
        body = b'{"hello":"world"}'
        assert verify_signature(body, sign(body), APP_SECRET) is True

    def test_rejects_a_tampered_body(self):
        body = b'{"hello":"world"}'
        assert verify_signature(b'{"hello":"evil"}', sign(body), APP_SECRET) is False

    def test_rejects_missing_header(self):
        assert verify_signature(b"{}", None, APP_SECRET) is False

    def test_rejects_malformed_header(self):
        assert verify_signature(b"{}", "sha1=abc", APP_SECRET) is False

    def test_skips_check_when_no_secret_configured(self):
        assert verify_signature(b"{}", None, None) is True

    def test_post_with_bad_signature_is_rejected(self, client, dispatcher):
        body = json.dumps(INBOUND_TEXT).encode()
        response = client.post(
            "/webhook/whatsapp",
            data=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=deadbeef"},
        )
        assert response.status_code == 403
        assert dispatcher.handled == []


class TestInboundProcessing:
    def _post(self, client, payload):
        body = json.dumps(payload).encode()
        return client.post(
            "/webhook/whatsapp",
            data=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sign(body)},
        )

    def test_text_message_reaches_the_dispatcher(self, client, dispatcher):
        response = self._post(client, INBOUND_TEXT)

        assert response.status_code == 200
        assert len(dispatcher.handled) == 1

        ref, text, profile = dispatcher.handled[0]
        assert ref.platform.value == "whatsapp"
        assert ref.platform_user_id == "15551234567"
        assert ref.key == "whatsapp:15551234567"
        assert text == "/video"
        assert profile.first_name == "Alice"

    def test_inbound_is_registered_for_the_24h_window(self, client, dispatcher):
        self._post(client, INBOUND_TEXT)
        assert len(dispatcher.registered) == 1

    def test_meta_retry_is_deduplicated(self, client, dispatcher):
        """Meta re-sends unacknowledged webhooks; the same wamid must run once."""
        self._post(client, INBOUND_TEXT)
        self._post(client, INBOUND_TEXT)
        assert len(dispatcher.handled) == 1

    def test_always_returns_200_so_meta_stops_retrying(self, client):
        assert self._post(client, {"object": "page", "entry": []}).status_code == 200

    def test_non_text_message_gets_a_helpful_reply(self, client, dispatcher):
        payload = json.loads(json.dumps(INBOUND_TEXT))
        message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        message.pop("text")
        message["type"] = "image"
        message["id"] = "wamid.IMAGE1"

        self._post(client, payload)

        assert dispatcher.handled == []
        assert dispatcher.unsupported[0][1] == "image"

    def test_status_callbacks_do_not_create_work(self, client, dispatcher):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"statuses": [
                {"id": "wamid.X", "status": "delivered", "recipient_id": "15551234567"}
            ]}}]}],
        }
        assert self._post(client, payload).status_code == 200
        assert dispatcher.handled == []


class TestPayloadParsing:
    def test_extracts_sender_and_profile(self):
        messages = extract_messages(INBOUND_TEXT)
        assert len(messages) == 1
        assert messages[0]["wa_id"] == "15551234567"
        assert messages[0]["text"] == "/video"
        assert messages[0]["profile_name"] == "Alice Smith"

    def test_interactive_button_reply_becomes_text(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"messages": [{
                "from": "15551234567",
                "id": "wamid.BTN",
                "type": "interactive",
                "interactive": {"type": "button_reply",
                                "button_reply": {"id": "quiz", "title": "Start quiz"}},
            }]}}]}],
        }
        message = extract_messages(payload)[0]
        assert message["type"] == "text"
        assert message["text"] == "Start quiz"

    def test_empty_payload_yields_nothing(self):
        assert extract_messages({}) == []
        assert extract_statuses({}) == []

    def test_extracts_delivery_errors(self):
        payload = {"entry": [{"changes": [{"value": {"statuses": [
            {"status": "failed", "recipient_id": "1", "errors": [{"code": 131047}]}
        ]}}]}]}
        assert extract_statuses(payload)[0]["errors"][0]["code"] == 131047


class TestProfileNameSplitting:
    @pytest.mark.parametrize("full,first,last", [
        ("Alice Smith", "Alice", "Smith"),
        ("Alice", "Alice", None),
        ("Alice Van Der Berg", "Alice", "Van Der Berg"),
        (None, None, None),
        ("", None, None),
    ])
    def test_splits(self, full, first, last):
        profile = split_profile_name(full)
        assert profile.first_name == first
        assert profile.last_name == last


class TestDeduplicator:
    def test_first_sighting_is_not_a_duplicate(self):
        assert MessageDeduplicator().seen_before("wamid.1") is False

    def test_second_sighting_is_a_duplicate(self):
        deduper = MessageDeduplicator()
        deduper.seen_before("wamid.1")
        assert deduper.seen_before("wamid.1") is True

    def test_evicts_oldest_beyond_the_limit(self):
        deduper = MessageDeduplicator(limit=2)
        deduper.seen_before("a")
        deduper.seen_before("b")
        deduper.seen_before("c")
        assert deduper.seen_before("a") is False   # evicted
        assert deduper.seen_before("c") is True

    def test_missing_id_is_never_a_duplicate(self):
        assert MessageDeduplicator().seen_before("") is False


class TestHealthEndpoint:
    def test_health_reports_enabled_platforms(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"
        assert "platforms" in response.get_json()

    def test_api_health_alias_exists_for_deploy_smoke_tests(self, client):
        assert client.get("/api/health").status_code == 200
