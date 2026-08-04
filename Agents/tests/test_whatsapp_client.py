"""
Tests for the WhatsApp Cloud API client, against a mocked Graph API.

These assert the exact request shapes Meta expects, so a payload regression is
caught here rather than in production.
"""
import json

import httpx
import pytest

from messaging.base import PermanentMessagingError, Platform, TransientMessagingError
from messaging.whatsapp_client import WhatsAppClient

SEND_OK = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": "15551234567", "wa_id": "15551234567"}],
    "messages": [{"id": "wamid.TEST123"}],
}


def make_client(handler, **kwargs):
    transport = httpx.MockTransport(handler)
    return WhatsAppClient(
        access_token="test-token",
        phone_number_id="111222333",
        client=httpx.AsyncClient(transport=transport),
        **kwargs,
    )


def error_response(status, code, message="boom", subcode=None):
    body = {"error": {"message": message, "type": "OAuthException", "code": code}}
    if subcode:
        body["error"]["error_subcode"] = subcode
    return httpx.Response(status, json=body)


@pytest.mark.asyncio
class TestSendMessage:
    async def test_posts_the_documented_text_payload(self):
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["auth"] = request.headers.get("Authorization")
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        result = await client.send_message("+1 (555) 123-4567", "hello")

        assert result.success is True
        assert result.message_id == "wamid.TEST123"
        assert captured["url"].endswith("/v21.0/111222333/messages")
        assert captured["auth"] == "Bearer test-token"
        assert captured["body"] == {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "15551234567",       # normalised: no '+', no punctuation
            "type": "text",
            "text": {"preview_url": False, "body": "hello"},
        }

    async def test_long_text_is_split_into_multiple_sends(self):
        bodies = []

        def handler(request):
            bodies.append(json.loads(request.content)["text"]["body"])
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        await client.send_message("15551234567", "word " * 2000)

        assert len(bodies) > 1
        assert all(len(body) <= client.max_text_chars for body in bodies)

    async def test_api_version_is_configurable(self):
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler, api_version="v23.0")
        await client.send_message("15551234567", "hi")
        assert "/v23.0/" in captured["url"]


@pytest.mark.asyncio
class TestSendVideo:
    async def test_sends_by_media_id(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        await client.send_video("15551234567", "media-id-123", "A caption")

        assert captured["body"]["type"] == "video"
        assert captured["body"]["video"] == {"id": "media-id-123", "caption": "A caption"}

    async def test_sends_by_link_when_ref_is_a_url(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        await client.send_video("15551234567", "https://cdn.example.com/v.mp4")

        assert captured["body"]["video"] == {"link": "https://cdn.example.com/v.mp4"}

    async def test_caption_is_truncated_to_the_platform_limit(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        await client.send_video("15551234567", "media-id", "x" * 5000)

        assert len(captured["body"]["video"]["caption"]) == client.max_caption_chars

    async def test_missing_media_ref_is_permanent(self):
        client = make_client(lambda r: httpx.Response(200, json=SEND_OK))
        with pytest.raises(PermanentMessagingError, match="No WhatsApp media id"):
            await client.send_video("15551234567", "")


@pytest.mark.asyncio
class TestErrorMapping:
    async def test_24h_window_error_is_permanent_with_template_advice(self):
        """131047 means the customer service window closed - retrying cannot help."""
        client = make_client(lambda r: error_response(400, 131047, "Re-engagement message"))

        with pytest.raises(PermanentMessagingError) as exc_info:
            await client.send_message("15551234567", "hi")

        assert exc_info.value.code == 131047
        assert "template" in exc_info.value.suggestion.lower()

    async def test_expired_token_is_permanent(self):
        client = make_client(lambda r: error_response(401, 190, "Session expired"))
        with pytest.raises(PermanentMessagingError) as exc_info:
            await client.send_message("15551234567", "hi")
        assert "token" in exc_info.value.suggestion.lower()

    async def test_rate_limit_is_transient(self):
        client = make_client(lambda r: error_response(400, 130429, "throughput reached"))
        with pytest.raises(TransientMessagingError):
            await client.send_message("15551234567", "hi")

    async def test_server_error_is_transient(self):
        client = make_client(lambda r: httpx.Response(503, json={}))
        with pytest.raises(TransientMessagingError):
            await client.send_message("15551234567", "hi")

    async def test_timeout_is_transient(self):
        def handler(request):
            raise httpx.ReadTimeout("timed out", request=request)

        client = make_client(handler)
        with pytest.raises(TransientMessagingError, match="timed out"):
            await client.send_message("15551234567", "hi")

    async def test_unknown_code_still_gets_a_hint(self):
        client = make_client(lambda r: error_response(400, 999999, "mystery"))
        with pytest.raises(PermanentMessagingError) as exc_info:
            await client.send_message("15551234567", "hi")
        assert "999999" in exc_info.value.suggestion


@pytest.mark.asyncio
class TestUploadVideo:
    async def test_rejects_files_over_the_16mb_cap(self, tmp_path):
        big = tmp_path / "big.mp4"
        big.write_bytes(b"0" * (17 * 1024 * 1024))

        client = make_client(lambda r: httpx.Response(200, json={"id": "x"}))
        with pytest.raises(PermanentMessagingError, match="at most 16 MB"):
            await client.upload_video(str(big))

    async def test_rejects_non_mp4(self, tmp_path):
        bad = tmp_path / "clip.avi"
        bad.write_bytes(b"0" * 1024)

        client = make_client(lambda r: httpx.Response(200, json={"id": "x"}))
        with pytest.raises(PermanentMessagingError, match="video/mp4"):
            await client.upload_video(str(bad))

    async def test_missing_file_is_permanent(self):
        client = make_client(lambda r: httpx.Response(200, json={"id": "x"}))
        with pytest.raises(PermanentMessagingError, match="not found"):
            await client.upload_video("/no/such/video.mp4")

    async def test_successful_upload_returns_media_id(self, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"0" * 2048)
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["content_type"] = request.headers.get("Content-Type", "")
            captured["raw"] = request.content
            return httpx.Response(200, json={"id": "media-abc-123"})

        client = make_client(handler)
        result = await client.upload_video(str(video))

        assert result.media_ref == "media-abc-123"
        assert captured["url"].endswith("/111222333/media")
        assert captured["content_type"].startswith("multipart/form-data")
        assert b"whatsapp" in captured["raw"]


@pytest.mark.asyncio
class TestTemplateAndReceipts:
    async def test_template_payload_carries_body_params(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=SEND_OK)

        client = make_client(handler)
        await client.send_template("15551234567", "daily_video_ready", "en_US", ["Alice", "Safety 101"])

        template = captured["body"]["template"]
        assert captured["body"]["type"] == "template"
        assert template["name"] == "daily_video_ready"
        assert template["language"] == {"code": "en_US"}
        assert template["components"][0]["parameters"] == [
            {"type": "text", "text": "Alice"},
            {"type": "text", "text": "Safety 101"},
        ]

    async def test_mark_read_posts_status(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"success": True})

        client = make_client(handler)
        await client.mark_read("wamid.ABC")

        assert captured["body"] == {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": "wamid.ABC",
        }

    async def test_mark_read_never_raises(self):
        client = make_client(lambda r: error_response(400, 100, "bad"))
        await client.mark_read("wamid.ABC")  # must not raise


class TestConstruction:
    def test_requires_access_token(self):
        with pytest.raises(ValueError, match="WHATSAPP_ACCESS_TOKEN"):
            WhatsAppClient(access_token="", phone_number_id="1")

    def test_requires_phone_number_id(self):
        with pytest.raises(ValueError, match="WHATSAPP_PHONE_NUMBER_ID"):
            WhatsAppClient(access_token="t", phone_number_id="")

    def test_declares_platform_limits(self):
        client = WhatsAppClient(access_token="t", phone_number_id="1")
        assert client.platform is Platform.WHATSAPP
        assert client.max_video_bytes == 16 * 1024 * 1024
        assert client.max_caption_chars == 1024
