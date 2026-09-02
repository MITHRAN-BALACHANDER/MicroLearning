"""
Tests for WhatsApp text formatting.

The invariants at the bottom are the valuable ones. WhatsApp shows an
unbalanced marker literally, but Telegram's Markdown parser rejects the whole
send with a 400 - so a stray asterisk in shared copy is a
delivered-versus-dropped bug on one channel and a cosmetic blemish on the other.
"""
import re

import pytest

from messaging import formatting as fmt


class TestMarkers:
    def test_bold_uses_a_single_asterisk(self):
        """Markdown's '**' renders as literal asterisks on WhatsApp."""
        assert fmt.bold("Welcome") == "*Welcome*"

    def test_italic_and_strike(self):
        assert fmt.italic("soon") == "_soon_"
        assert fmt.strike("old") == "~old~"

    def test_bullets_avoid_the_asterisk_marker(self):
        """
        WhatsApp allows '*' or '-'. A line-leading '*' is an unclosed bold
        entity to Telegram, which 400s the send, so '-' is the portable one.
        """
        assert fmt.bullets(["one", "two"]) == "- one\n- two"

    def test_numbered_list(self):
        assert fmt.numbered(["first", "second"]) == "1. first\n2. second"

    def test_quote_marks_every_line(self):
        assert fmt.quote("a\nb") == "> a\n> b"

    def test_field_renders_a_bold_label(self):
        assert fmt.field("Score", "8/10") == "*Score:* 8/10"


class TestSanitize:
    def test_strips_every_markup_character(self):
        assert fmt.sanitize("a *b* _c_ ~d~ `e`") == "a b c d e"

    def test_handles_none_and_empty(self):
        assert fmt.sanitize(None) == ""
        assert fmt.sanitize("") == ""

    def test_unbalanced_marker_cannot_survive(self):
        """The real failure mode: one stray marker in model output."""
        assert "*" not in fmt.sanitize("The answer is *important")

    def test_snake_case_underscores_are_removed(self):
        assert fmt.sanitize("see user_profile_id") == "see userprofileid"


class TestParagraphs:
    def test_joins_with_a_blank_line_and_drops_empties(self):
        assert fmt.paragraphs("one", "", None, "  ", "two") == "one\n\ntwo"

    def test_single_part_is_unchanged(self):
        assert fmt.paragraphs("only") == "only"


class TestTruncate:
    def test_leaves_short_text_alone(self):
        assert fmt.truncate("short", 20) == "short"

    def test_cuts_on_a_word_boundary(self):
        assert fmt.truncate("the quick brown fox jumps", 20) == "the quick brown..."

    def test_never_exceeds_the_limit(self):
        assert len(fmt.truncate("x" * 100, 30)) <= 30


def _authored_copy():
    """Every module-level message constant the dispatcher sends."""
    import dispatcher

    for name in dir(dispatcher):
        if name.isupper():
            value = getattr(dispatcher, name)
            if isinstance(value, str):
                yield name, value


def _inline_markers(text, char):
    """
    Count markers that are meant to format.

    Two things are excluded. A '-' or '*' opening a line is a list bullet, not
    an opening marker, so it is legitimately unpaired. And '{placeholder}'
    names are substituted before sending, so an underscore in one is not copy -
    whatever replaces it is sanitized separately.
    """
    text = re.sub(r"\{[^}]*\}", "", text)
    total = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("* ", "- ")):
            stripped = stripped[2:]
        total += stripped.count(char)
    return total


class TestAuthoredCopyIsValidWhatsApp:
    @pytest.mark.parametrize("char", ["*", "_", "~"])
    def test_markers_are_balanced(self, char):
        for name, text in _authored_copy():
            assert _inline_markers(text, char) % 2 == 0, (
                f"dispatcher.{name} has an unbalanced '{char}': {text!r}"
            )

    def test_no_markdown_bold_leaked_in(self):
        """'**bold**' is a Markdown habit that renders literally on WhatsApp."""
        for name, text in _authored_copy():
            assert "**" not in text, f"dispatcher.{name} uses Markdown '**'"

    def test_no_markdown_headings_or_links(self):
        for name, text in _authored_copy():
            assert not text.lstrip().startswith("#"), f"dispatcher.{name} uses a '#' heading"
            assert "](" not in text, f"dispatcher.{name} uses a Markdown link"

    def test_no_asterisk_bullets_in_shared_copy(self):
        """A line-leading '*' would make Telegram reject the message."""
        for name, text in _authored_copy():
            for line in text.splitlines():
                assert not line.lstrip().startswith("* "), (
                    f"dispatcher.{name} uses a '*' bullet; use '-' for Telegram compatibility"
                )


class TestMenusFitMetasLimits:
    """Meta rejects the whole message if a title or row overruns."""

    def test_button_menus_fit(self):
        from dispatcher import AFTER_QUIZ_MENU, AFTER_LESSON_MENU, START_LEARNING_MENU
        from messaging.whatsapp_client import WhatsAppClient

        for menu in (AFTER_LESSON_MENU, AFTER_QUIZ_MENU, START_LEARNING_MENU):
            assert len(menu) <= WhatsAppClient.max_buttons
            for choice in menu:
                assert len(choice.title) <= WhatsAppClient.max_button_title_chars

    def test_main_menu_fits_a_list(self):
        from dispatcher import MAIN_MENU
        from messaging.whatsapp_client import WhatsAppClient

        assert len(MAIN_MENU) <= WhatsAppClient.max_choices
        for choice in MAIN_MENU:
            assert len(choice.title) <= WhatsAppClient.max_choice_title_chars
            assert len(choice.description) <= WhatsAppClient.max_choice_description_chars

    def test_menu_header_and_footer_fit(self):
        from dispatcher import MENU_FOOTER, MENU_HEADER
        from messaging.whatsapp_client import WhatsAppClient

        assert len(MENU_HEADER) <= WhatsAppClient.max_interactive_header_chars
        assert len(MENU_FOOTER) <= WhatsAppClient.max_interactive_footer_chars

    def test_choice_ids_are_routable_commands(self):
        """A button whose id is not a command would dead-end the learner."""
        from dispatcher import (
            AFTER_QUIZ_MENU,
            AFTER_LESSON_MENU,
            MAIN_MENU,
            START_LEARNING_MENU,
        )

        known = {"start", "lesson", "quiz", "ask", "progress", "docs", "help", "menu"}
        for menu in (MAIN_MENU, AFTER_LESSON_MENU, AFTER_QUIZ_MENU, START_LEARNING_MENU):
            for choice in menu:
                assert choice.id in known, f"'{choice.id}' is not a dispatcher command"


EMOJI = re.compile(
    # Written as escapes so this guard does not itself contain emoji.
    "["
    "\U0001F000-\U0001FAFF"   # pictographs, emoticons, transport
    "\u2600-\u27BF"           # misc symbols and dingbats
    "\u2B00-\u2BFF"           # arrows and stars, emoji presentation
    "\uFE0F\u20E3"            # variation selector, combining keycap
    "]"
)


class TestNoEmoji:
    """
    The product does not use emoji.

    Worth a test rather than a code review note: they arrive one at a time in
    new copy, and they are invisible in a diff until someone reads the string.
    """

    def test_learner_facing_copy_has_none(self):
        for name, text in _authored_copy():
            found = EMOJI.findall(text)
            assert not found, f"dispatcher.{name} contains emoji: {found}"

    def test_format_badges_have_none(self):
        for content_type in list(fmt.FORMAT_LABELS) + ["podcast", None]:
            badge = fmt.format_badge(content_type, 300)
            assert not EMOJI.findall(badge), f"format_badge({content_type!r}) -> {badge!r}"

    def test_messaging_modules_have_none(self):
        """Covers the clients and the formatting helpers themselves."""
        import pathlib

        root = pathlib.Path(__file__).resolve().parent.parent
        targets = list((root / "messaging").glob("*.py")) + [
            root / "dispatcher.py",
            root / "whatsapp_webhook.py",
        ]
        for path in targets:
            found = EMOJI.findall(path.read_text(encoding="utf-8"))
            assert not found, f"{path.name} contains emoji: {found}"
