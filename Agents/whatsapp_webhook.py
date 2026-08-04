"""
WhatsApp Cloud API webhook server.

Meta delivers inbound messages by POSTing to a public HTTPS callback URL. Two
rules drive the design here:

1. **Verification** - Meta first sends a GET with `hub.verify_token`; we must
   echo `hub.challenge` verbatim or the webhook cannot be saved.
2. **Fast 200** - Meta retries any delivery that is not acknowledged quickly,
   which would double-process messages. We therefore validate, deduplicate,
   hand the work to a background event loop, and return 200 immediately.

Payloads are authenticated with `X-Hub-Signature-256` (HMAC-SHA256 of the raw
body using the Meta app secret).
"""
import hashlib
import hmac
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from loguru import logger

from config import settings
from dispatcher import Profile
from messaging.base import Platform, UserRef

# Meta retries webhooks; remember recent message ids so a retry is a no-op.
_SEEN_LIMIT = 2000


class MessageDeduplicator:
    """Bounded set of processed message ids (wamids)."""

    def __init__(self, limit: int = _SEEN_LIMIT):
        self.limit = limit
        self._seen: "OrderedDict[str, None]" = OrderedDict()

    def seen_before(self, message_id: str) -> bool:
        if not message_id:
            return False
        if message_id in self._seen:
            self._seen.move_to_end(message_id)
            return True
        self._seen[message_id] = None
        while len(self._seen) > self.limit:
            self._seen.popitem(last=False)
        return False


def verify_signature(raw_body: bytes, signature_header: Optional[str], app_secret: Optional[str]) -> bool:
    """
    Validate Meta's X-Hub-Signature-256 header.

    Returns True when the signature matches. When no app secret is configured
    the check is skipped (development only) and the caller logs a warning.
    """
    if not app_secret:
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header[len("sha256="):])


def extract_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten a Cloud API webhook body into a list of inbound messages.

    Shape: entry[] -> changes[] -> value.messages[] with value.contacts[]
    carrying the sender's profile name.
    """
    messages: List[Dict[str, Any]] = []

    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}

            # Map wa_id -> profile name from the contacts block
            names = {}
            for contact in value.get("contacts", []) or []:
                wa_id = contact.get("wa_id")
                profile_name = (contact.get("profile") or {}).get("name")
                if wa_id:
                    names[wa_id] = profile_name

            for message in value.get("messages", []) or []:
                sender = message.get("from")
                if not sender:
                    continue

                message_type = message.get("type", "unknown")
                text = ""

                if message_type == "text":
                    text = (message.get("text") or {}).get("body", "")
                elif message_type == "interactive":
                    interactive = message.get("interactive") or {}
                    reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
                    text = reply.get("title") or reply.get("id") or ""
                    message_type = "text" if text else message_type
                elif message_type == "button":
                    text = (message.get("button") or {}).get("text", "")
                    message_type = "text" if text else message_type

                messages.append({
                    "wa_id": sender,
                    "message_id": message.get("id"),
                    "type": message_type,
                    "text": text,
                    "profile_name": names.get(sender),
                    "timestamp": message.get("timestamp"),
                })

    return messages


def extract_statuses(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Delivery/read receipts and per-message errors, for logging."""
    statuses = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            for status in (change.get("value", {}) or {}).get("statuses", []) or []:
                statuses.append(status)
    return statuses


def split_profile_name(full_name: Optional[str]) -> Profile:
    """WhatsApp only exposes a single display name; split it best-effort."""
    if not full_name:
        return Profile()
    parts = full_name.strip().split(maxsplit=1)
    return Profile(
        username=None,
        first_name=parts[0] if parts else None,
        last_name=parts[1] if len(parts) > 1 else None,
    )


def create_app(dispatcher=None, worker=None, orchestrator=None) -> Flask:
    """
    Build the webhook Flask app.

    Args:
        dispatcher: CommandDispatcher handling inbound messages
        worker: AsyncWorker used to run agent coroutines off the request thread
        orchestrator: optional, exposed on /health for diagnostics
    """
    app = Flask(__name__)
    deduper = MessageDeduplicator()
    webhook_path = settings.WHATSAPP_WEBHOOK_PATH

    if not settings.WHATSAPP_APP_SECRET:
        logger.warning(
            "WHATSAPP_APP_SECRET is not set - inbound webhook signatures will NOT be "
            "verified. Set it before going to production."
        )

    @app.get("/health")
    def health():
        """Liveness probe (also used by the Docker HEALTHCHECK)."""
        body = {
            "status": "ok",
            "platforms": list(settings.ENABLED_PLATFORMS),
        }
        if orchestrator is not None:
            try:
                body["agents"] = orchestrator.get_all_agents_status()
            except Exception as exc:  # noqa: BLE001
                body["agents_error"] = str(exc)
        return jsonify(body), 200

    # Meta's CD smoke tests hit /api/health
    app.add_url_rule("/api/health", "api_health", health, methods=["GET"])

    @app.get(webhook_path)
    def verify_webhook():
        """
        Meta's one-time verification handshake.

        Echo hub.challenge as plain text when hub.verify_token matches
        WHATSAPP_VERIFY_TOKEN, otherwise 403.
        """
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge", "")

        if mode == "subscribe" and token and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified by Meta")
            return challenge, 200, {"Content-Type": "text/plain"}

        logger.warning(
            f"WhatsApp webhook verification failed (mode={mode}, token_matched="
            f"{token == settings.WHATSAPP_VERIFY_TOKEN})"
        )
        return "Verification failed", 403

    @app.post(webhook_path)
    def receive_webhook():
        """Accept inbound messages, acknowledge fast, process in background."""
        raw_body = request.get_data()

        if not verify_signature(
            raw_body, request.headers.get("X-Hub-Signature-256"), settings.WHATSAPP_APP_SECRET
        ):
            logger.warning("Rejected WhatsApp webhook with an invalid signature")
            return jsonify({"error": "invalid signature"}), 403

        payload = request.get_json(silent=True) or {}

        if payload.get("object") != "whatsapp_business_account":
            # Not ours; still 200 so Meta does not retry forever.
            return jsonify({"status": "ignored"}), 200

        for status in extract_statuses(payload):
            if status.get("errors"):
                logger.warning(
                    f"WhatsApp delivery error for {status.get('recipient_id')}: {status['errors']}"
                )
            else:
                logger.debug(
                    f"WhatsApp status {status.get('status')} for {status.get('recipient_id')}"
                )

        accepted = 0
        for message in extract_messages(payload):
            if deduper.seen_before(message["message_id"]):
                logger.debug(f"Skipping duplicate WhatsApp message {message['message_id']}")
                continue

            if dispatcher is None or worker is None:
                logger.error("Webhook received a message but no dispatcher is wired up")
                continue

            worker.submit(_process(dispatcher, message))
            accepted += 1

        return jsonify({"status": "received", "accepted": accepted}), 200

    return app


async def _process(dispatcher, message: Dict[str, Any]) -> None:
    """Handle one inbound WhatsApp message on the background loop."""
    ref = UserRef(Platform.WHATSAPP, message["wa_id"])
    profile = split_profile_name(message.get("profile_name"))

    # Records the inbound timestamp that opens WhatsApp's 24h reply window
    dispatcher.register_inbound(ref, profile)
    await dispatcher.router.mark_read(ref, message.get("message_id"))

    if message["type"] != "text" or not message["text"].strip():
        await dispatcher.handle_unsupported(ref, message["type"])
        return

    logger.info(f"WhatsApp inbound from {ref}: {message['text'][:80]}")
    await dispatcher.handle_text(ref, message["text"], profile)


def run_webhook_server(app: Flask, host: str = None, port: int = None) -> None:
    """
    Serve the webhook.

    Prefers waitress (a production WSGI server that runs on Windows and Linux)
    and falls back to Flask's development server when it is not installed.
    """
    host = host or settings.WEBHOOK_HOST
    port = port or settings.WEBHOOK_PORT

    try:
        from waitress import serve

        logger.info(f"Webhook listening on http://{host}:{port} (waitress)")
        serve(app, host=host, port=port, threads=8)
    except ImportError:
        logger.warning(
            "waitress is not installed - falling back to the Flask development "
            "server. Install waitress for production use."
        )
        logger.info(f"Webhook listening on http://{host}:{port} (flask dev server)")
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
