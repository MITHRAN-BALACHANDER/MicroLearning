"""
WhatsApp text formatting.

Meta's supported syntax (https://faq.whatsapp.com/539178204879377):

    *bold* _italic_ ~strikethrough~
    ```monospace``` `inline code` > blockquote
    * bulleted item 1. numbered item

This is deliberately **not** Markdown, and the differences bite:

  - ``**bold**`` renders as literal asterisks; WhatsApp wants a single ``*``.
  - ``#`` headings do nothing at all - use bold for a heading.
  - ``[text](url)`` shows the brackets; WhatsApp linkifies bare URLs itself.
  - A marker only formats when it is *balanced* and hugs the text, so
    ``* not bold *`` stays literal.

Telegram's legacy Markdown happens to use the same ``*bold*`` and ``_italic_``
markers, which is why one authored string serves both channels - see
``TelegramClient.send_message`` for how it is parsed there.

Everything a language model or a database wrote goes through :func:`sanitize`
first. A stray underscore in "snake_case" or an unclosed asterisk from Gemini
would otherwise swallow the rest of the message into italics, or make
Telegram reject the send outright.
"""
from typing import Iterable, List, Optional

# The four characters WhatsApp (and Telegram's Markdown) treat as markup.
MARKUP_CHARS = "*_~`"

# A visual divider. WhatsApp has no horizontal rule, and a row of dashes reads
# as a bulleted list, so use box-drawing characters.
DIVIDER = "─" * 12


def bold(text) -> str:
    """*bold* - WhatsApp's only heading mechanism."""
    return f"*{text}*"


def italic(text) -> str:
    """_italic_ - good for asides and instructions."""
    return f"_{text}_"


def strike(text) -> str:
    """~strikethrough~"""
    return f"~{text}~"


def mono(text) -> str:
    """```monospace``` block."""
    return f"```{text}```"


def code(text) -> str:
    """`inline code`"""
    return f"`{text}`"


def quote(text) -> str:
    """A blockquote; each line needs its own '>' marker."""
    return "\n".join(f"> {line}" for line in str(text).splitlines() or [""])


def bullets(items: Iterable, marker: str = "-") -> str:
    """
    A bulleted list.

    WhatsApp accepts either '*' or '-' at the start of a line. We use '-'
    because the same string is sent to Telegram, whose Markdown parser reads a
    line-leading '*' as an unclosed bold entity and rejects the whole message
    with a 400. '-' is inert there and renders identically on WhatsApp.
    """
    return "\n".join(f"{marker} {item}" for item in items)


def numbered(items: Iterable, start: int = 1) -> str:
    """A numbered list ('1. item')."""
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start))


def sanitize(text: Optional[str]) -> str:
    """
    Strip formatting markers from text we did not author.

    Model output, document titles and learner answers get embedded in messages
    we *do* format. One unbalanced marker in there changes how the rest of the
    message renders - and on Telegram it is a hard 400 from the Bot API - so
    the markers come out before the text goes in.
    """
    if not text:
        return ""
    cleaned = str(text)
    for char in MARKUP_CHARS:
        cleaned = cleaned.replace(char, "")
    return cleaned


def paragraphs(*parts: Optional[str]) -> str:
    """
    Join non-empty parts with a blank line between them.

    Saves every caller from threading "\\n\\n" through conditionals and
    accidentally leaving a double gap when a part is empty.
    """
    return "\n\n".join(str(p).strip() for p in parts if p and str(p).strip())


def field(label: str, value) -> str:
    """A '*Label:* value' line, the workhorse of the status messages."""
    return f"{bold(str(label) + ':')} {value}"


def section(title: str, body: str) -> str:
    """A bold title with its body underneath."""
    return f"{bold(title)}\n{body}"


def truncate(text: Optional[str], limit: int, suffix: str = "...") -> str:
    """
    Cut text to `limit` characters.

    Trims to a word boundary when one is reasonably close, so a truncated
    sentence does not end mid-word.
    """
    text = str(text or "")
    if len(text) <= limit:
        return text
    if limit <= len(suffix):
        return text[:limit]

    cut = text[: limit - len(suffix)]
    space = cut.rfind(" ")
    if space > limit // 2:
        cut = cut[:space]
    return cut.rstrip() + suffix


def lines(*parts: Optional[str]) -> List[str]:
    """Drop empties from a list of lines - used when building messages."""
    return [str(p) for p in parts if p is not None and str(p) != ""]


# ---------------------------------------------------------------------------
# Lesson formats
# ---------------------------------------------------------------------------
# A lesson can arrive as video, audio, a document, or a short read. The learner
# should be able to tell which before they open it - a five-minute video and a
# five-minute read are different commitments, and one of them needs headphones.

FORMAT_LABELS = {
    "video": "Video",
    "audio": "Audio",
    "document": "Document",
    "text": "Read",
}


def duration_text(seconds) -> str:
    """Human-readable length: '4 min' rather than '00:04:12'."""
    if not seconds:
        return ""
    minutes = int(seconds) // 60
    if minutes < 1:
        return "under a minute"
    return f"{minutes} min"


def format_badge(content_type, seconds=None) -> str:
    """
    The 'Audio - 5 min' line that heads a lesson.

    Falls back to the type's own name for anything unrecognised rather than
    hiding it, so a new format shows up as itself instead of vanishing.
    """
    key = str(content_type or "video").lower()
    label = FORMAT_LABELS.get(key) or str(content_type or "Lesson").title()
    length = duration_text(seconds)
    return f"{label} - {length}" if length else label
