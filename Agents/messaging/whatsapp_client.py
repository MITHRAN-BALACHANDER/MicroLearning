"""
WhatsApp Cloud API implementation of MessagingClient (Meta Graph API).

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api

Two constraints shape this client and have no Telegram equivalent:

1. **24-hour customer service window** - free-form messages may only be sent
   within 24h of the user's last inbound message. Outside it, Meta rejects the
   send with error 131047 and only an approved *template* message may be used.
2. **16 MB media cap** - noticeably lower than Telegram's 50 MB.
"""
import mimetypes
import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from messaging.base import (
    MessagingClient,
    OutboundResult,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
    normalize_wa_id,
)

# Graph API error codes that are worth retrying.
TRANSIENT_CODES = {
    0,       # unknown / temporary
    1,       # unknown API error
    2,       # temporary Graph outage
    4,       # application request limit reached
    80007,   # rate limit hit
    130429,  # Cloud API message throughput reached
    131048,  # spam rate limit hit
    131056,  # pair rate limit hit
    133016,  # temporary account lock
}

# Codes that need an operator action, mapped to actionable advice.
PERMANENT_CODE_HINTS = {
    131047: (
        "Outside the 24-hour customer service window. The user must message the "
        "business first, or you must send an approved template message "
        "(see WHATSAPP_TEMPLATE_DAILY_VIDEO)."
    ),
    131026: "Recipient is not a WhatsApp user, or cannot receive messages right now.",
    131030: (
        "Recipient is not on the test allow-list. While the app is in Development mode "
        "add their number under WhatsApp > API Setup > 'To' > Manage phone number list, "
        "or switch the app to Live mode."
    ),
    131051: "Unsupported message type for this recipient.",
    131052: "Media download failed - Meta could not fetch the media URL.",
    131053: "Media upload failed - check the file format and size (video max 16 MB).",
    190: "Access token expired or revoked. Generate a new permanent system-user token.",
    100: "Invalid parameter - check phone number ID and payload shape.",
    132000: "Template parameter count mismatch.",
    132001: "Template does not exist in this WhatsApp Business Account, or is not approved.",
    132005: "Template text is longer than allowed.",
    132007: "Template content violates policy.",
    132012: "Template parameter format mismatch.",
    132015: "Template is paused due to low quality.",
    133010: "Phone number is not registered on the Cloud API.",
    368: "Temporarily blocked for policy violations.",
}


class WhatsAppClient(MessagingClient):
    """Sends and uploads media through the WhatsApp Cloud API."""

    platform = Platform.WHATSAPP
    max_text_chars = 4096      # WhatsApp text body limit
    max_caption_chars = 1024   # media caption limit
    max_video_bytes = 16 * 1024 * 1024  # Cloud API video cap

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        *,
        api_base: str = "https://graph.facebook.com",
        api_version: str = "v21.0",
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        if not access_token:
            raise ValueError("WHATSAPP_ACCESS_TOKEN is required to use the WhatsApp client")
        if not phone_number_id:
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID is required to use the WhatsApp client")

        self.access_token = access_token
        self.phone_number_id = str(phone_number_id)
        self.api_root = f"{api_base.rstrip('/')}/{api_version}"
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None

    # -- plumbing ---------------------------------------------------------

    @property
    def messages_url(self) -> str:
        return f"{self.api_root}/{self.phone_number_id}/messages"

    @property
    def media_url(self) -> str:
        return f"{self.api_root}/{self.phone_number_id}/media"

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    @property
    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = await self._http().post(
                url,
                json=payload,
                headers={**self._auth_headers, "Content-Type": "application/json"},
            )
        except httpx.TimeoutException as exc:
            raise TransientMessagingError(
                f"WhatsApp request timed out: {exc}",
                platform=self.platform,
                suggestion="Retry; check network egress to graph.facebook.com.",
            ) from exc
        except httpx.HTTPError as exc:
            raise TransientMessagingError(
                f"WhatsApp network error: {exc}",
                platform=self.platform,
            ) from exc

        return self._parse_response(response)

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.is_success:
            return body

        error = body.get("error", {}) if isinstance(body, dict) else {}
        code = error.get("code")
        subcode = error.get("error_subcode")
        message = error.get("message") or response.text or f"HTTP {response.status_code}"
        details = error.get("error_data", {}).get("details") if isinstance(error.get("error_data"), dict) else None
        if details:
            message = f"{message} ({details})"

        full = f"WhatsApp API error {code or response.status_code}: {message}"

        if code in TRANSIENT_CODES or response.status_code >= 500 or response.status_code == 429:
            raise TransientMessagingError(
                full,
                platform=self.platform,
                code=code,
                suggestion="Temporary Meta-side issue or rate limit - retry with backoff.",
            )

        raise PermanentMessagingError(
            full,
            platform=self.platform,
            code=code,
            suggestion=PERMANENT_CODE_HINTS.get(
                code, f"Check the Cloud API error reference for code {code} (subcode {subcode})."
            ),
        )

    @staticmethod
    def _message_id(body: Dict[str, Any]) -> Optional[str]:
        messages = body.get("messages") or []
        if messages and isinstance(messages, list):
            return messages[0].get("id")
        return None

    # -- outbound ---------------------------------------------------------

    async def send_message(self, to: str, text: str) -> OutboundResult:
        recipient = normalize_wa_id(to)
        message_id = None

        for part in self.split_message(text):
            if not part.strip():
                continue
            body = await self._post_json(
                self.messages_url,
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "text",
                    "text": {"preview_url": False, "body": part},
                },
            )
            message_id = self._message_id(body) or message_id

        return OutboundResult(success=True, platform=self.platform, message_id=message_id)

    async def send_video(self, to: str, media_ref: str, caption: str = "") -> OutboundResult:
        if not media_ref:
            raise PermanentMessagingError(
                "No WhatsApp media id available for this video",
                platform=self.platform,
                suggestion="Upload the video once with VideoUploadAgent to obtain a media id.",
            )

        # A media reference is either an uploaded media id or a public URL.
        if str(media_ref).startswith(("http://", "https://")):
            video_payload: Dict[str, Any] = {"link": media_ref}
        else:
            video_payload = {"id": media_ref}

        caption = self.truncate_caption(caption)
        if caption:
            video_payload["caption"] = caption

        body = await self._post_json(
            self.messages_url,
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalize_wa_id(to),
                "type": "video",
                "video": video_payload,
            },
        )

        return OutboundResult(
            success=True,
            platform=self.platform,
            message_id=self._message_id(body),
            media_ref=media_ref,
        )

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        body_params: Optional[List[str]] = None,
    ) -> OutboundResult:
        """
        Send an approved template message. This is the only way to reach a user
        outside the 24-hour customer service window (e.g. the daily video nudge).
        """
        template: Dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }

        if body_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(value)} for value in body_params],
                }
            ]

        body = await self._post_json(
            self.messages_url,
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalize_wa_id(to),
                "type": "template",
                "template": template,
            },
        )

        return OutboundResult(success=True, platform=self.platform, message_id=self._message_id(body))

    async def upload_video(self, file_path: str, *, staging_chat_id: Optional[str] = None) -> OutboundResult:
        """
        Upload a video to Meta's media store once and return the media id.

        The id is reusable for unlimited sends but **expires after 30 days**,
        so callers should be ready to re-upload.
        """
        if not os.path.exists(file_path):
            raise PermanentMessagingError(
                f"Video file not found: {file_path}",
                platform=self.platform,
                suggestion="Check the file path stored on the video record.",
            )

        size = os.path.getsize(file_path)
        if size > self.max_video_bytes:
            raise PermanentMessagingError(
                f"Video is {size / 1024 / 1024:.1f} MB; WhatsApp accepts at most "
                f"{self.max_video_bytes / 1024 / 1024:.0f} MB",
                platform=self.platform,
                suggestion="Compress the video, or host it publicly and store the URL as the media reference.",
            )

        mime_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
        if mime_type not in ("video/mp4", "video/3gpp"):
            raise PermanentMessagingError(
                f"WhatsApp only accepts video/mp4 and video/3gpp, got {mime_type}",
                platform=self.platform,
                suggestion="Re-encode the clip as H.264/AAC MP4.",
            )

        # Buffer the file before touching the network: filesystem I/O and HTTP
        # I/O in the same async context is what caused the original upload hangs.
        with open(file_path, "rb") as handle:
            buffer = handle.read()

        try:
            response = await self._http().post(
                self.media_url,
                headers=self._auth_headers,
                data={"messaging_product": "whatsapp", "type": mime_type},
                files={"file": (os.path.basename(file_path), buffer, mime_type)},
                timeout=max(self.timeout, 300.0),
            )
        except httpx.TimeoutException as exc:
            raise TransientMessagingError(
                f"WhatsApp media upload timed out: {exc}",
                platform=self.platform,
            ) from exc
        except httpx.HTTPError as exc:
            raise TransientMessagingError(
                f"WhatsApp media upload network error: {exc}",
                platform=self.platform,
            ) from exc

        body = self._parse_response(response)
        media_id = body.get("id")
        if not media_id:
            raise PermanentMessagingError(
                "WhatsApp accepted the upload but returned no media id",
                platform=self.platform,
            )

        logger.info(f"WhatsApp upload cached media id for {os.path.basename(file_path)}")
        return OutboundResult(success=True, platform=self.platform, media_ref=media_id)

    async def mark_read(self, message_id: str) -> None:
        """Show the blue ticks so learners know the bot received their message."""
        if not message_id:
            return
        try:
            await self._post_json(
                self.messages_url,
                {"messaging_product": "whatsapp", "status": "read", "message_id": message_id},
            )
        except Exception as exc:  # read receipts are cosmetic - never fail a turn
            logger.debug(f"Could not mark WhatsApp message read: {exc}")
