"""Unit tests for the platform abstraction: UserRef keys, splitting, routing."""
import pytest

from messaging.base import (
    OutboundResult,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
    UserRef,
    normalize_wa_id,
    split_text,
)
from messaging.router import MessagingRouter


class TestPlatform:
    def test_parse_accepts_strings_and_enums(self):
        assert Platform.parse("whatsapp") is Platform.WHATSAPP
        assert Platform.parse("TELEGRAM") is Platform.TELEGRAM
        assert Platform.parse(Platform.WHATSAPP) is Platform.WHATSAPP

    def test_parse_rejects_unknown(self):
        with pytest.raises(ValueError, match="Unknown platform"):
            Platform.parse("signal")


class TestUserRef:
    def test_telegram_key_is_bare_for_backwards_compatibility(self):
        """Existing rows store a raw chat id, so telegram keys must not change."""
        assert UserRef(Platform.TELEGRAM, "6437411483").key == "6437411483"

    def test_whatsapp_key_is_namespaced(self):
        assert UserRef(Platform.WHATSAPP, "15551234567").key == "whatsapp:15551234567"

    def test_same_id_on_two_platforms_does_not_collide(self):
        telegram = UserRef(Platform.TELEGRAM, "15551234567")
        whatsapp = UserRef(Platform.WHATSAPP, "15551234567")
        assert telegram.key != whatsapp.key

    def test_round_trips_through_key(self):
        for ref in (UserRef(Platform.TELEGRAM, "123"), UserRef(Platform.WHATSAPP, "15551234567")):
            assert UserRef.from_key(ref.key) == ref

    def test_whatsapp_helper_strips_formatting(self):
        assert UserRef.whatsapp("+1 (555) 123-4567").platform_user_id == "15551234567"

    def test_is_hashable_for_dict_keys(self):
        assert {UserRef(Platform.WHATSAPP, "1")} == {UserRef(Platform.WHATSAPP, "1")}


class TestNormalizeWaId:
    @pytest.mark.parametrize("raw,expected", [
        ("+15551234567", "15551234567"),
        ("1 555 123 4567", "15551234567"),
        ("15551234567", "15551234567"),
    ])
    def test_normalizes(self, raw, expected):
        assert normalize_wa_id(raw) == expected


class TestSplitText:
    def test_short_text_is_untouched(self):
        assert split_text("hello", 100) == ["hello"]

    def test_every_chunk_respects_the_limit(self):
        text = "word " * 500
        chunks = split_text(text, 100)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_prefers_paragraph_boundaries(self):
        text = "a" * 60 + "\n\n" + "b" * 60
        chunks = split_text(text, 80)
        assert chunks[0] == "a" * 60

    def test_no_content_is_lost(self):
        text = "alpha beta gamma delta epsilon " * 40
        joined = " ".join(split_text(text, 90)).replace("  ", " ")
        assert "epsilon" in joined
        assert len(joined) >= len(text.strip()) - 40

    def test_handles_text_with_no_break_opportunity(self):
        chunks = split_text("x" * 250, 100)
        assert [len(c) for c in chunks] == [100, 100, 50]


@pytest.mark.asyncio
class TestMessagingRouter:
    async def test_routes_to_the_platform_on_the_ref(self, router, fake_telegram_client,
                                                     fake_whatsapp_client):
        await router.send_message(UserRef(Platform.WHATSAPP, "15551234567"), "hi wa")
        await router.send_message(UserRef(Platform.TELEGRAM, "999"), "hi tg")

        assert fake_whatsapp_client.messages == [("15551234567", "hi wa")]
        assert fake_telegram_client.messages == [("999", "hi tg")]

    async def test_disabled_platform_raises(self, fake_telegram_client):
        telegram_only = MessagingRouter({Platform.TELEGRAM: fake_telegram_client})
        with pytest.raises(PermanentMessagingError, match="not enabled"):
            telegram_only.client_for(UserRef(Platform.WHATSAPP, "1"))

    async def test_retries_transient_failures(self, router, fake_whatsapp_client, monkeypatch):
        import asyncio

        # Skip the real backoff delay without recursing into the patched sleep
        real_sleep = asyncio.sleep

        async def no_delay(*_args, **_kwargs):
            await real_sleep(0)

        monkeypatch.setattr("messaging.router.asyncio.sleep", no_delay)
        calls = {"n": 0}

        async def flaky(to, text):
            calls["n"] += 1
            if calls["n"] < 3:
                raise TransientMessagingError("rate limited")
            return OutboundResult(success=True, platform=Platform.WHATSAPP, message_id="ok")

        fake_whatsapp_client.send_message = flaky
        result = await router.send_message(UserRef(Platform.WHATSAPP, "1"), "hello")

        assert result.success is True
        assert result.attempts == 3

    async def test_does_not_retry_permanent_failures(self, router, fake_whatsapp_client):
        calls = {"n": 0}

        async def rejected(to, text):
            calls["n"] += 1
            raise PermanentMessagingError("24h window closed", suggestion="use a template")

        fake_whatsapp_client.send_message = rejected
        result = await router.send_message(UserRef(Platform.WHATSAPP, "1"), "hello")

        assert result.success is False
        assert calls["n"] == 1
        assert result.suggestion == "use a template"

    async def test_send_failure_never_raises(self, router, fake_whatsapp_client):
        fake_whatsapp_client.fail_with = RuntimeError("boom")
        result = await router.send_message(UserRef(Platform.WHATSAPP, "1"), "hello")
        assert result.success is False

    async def test_broadcast_spans_platforms(self, router, fake_telegram_client,
                                             fake_whatsapp_client):
        refs = [UserRef(Platform.TELEGRAM, "1"), UserRef(Platform.WHATSAPP, "2")]
        results = await router.broadcast(refs, "announcement")

        assert all(r.success for r in results.values())
        assert len(fake_telegram_client.messages) == 1
        assert len(fake_whatsapp_client.messages) == 1
