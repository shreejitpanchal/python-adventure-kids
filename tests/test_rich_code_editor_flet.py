import flet as ft

from app.ui.components.rich_code_editor_flet import RichCodeEditor, tokenize
from app.ui.theme_flet import get_preset


class FakePage:
    def __init__(self) -> None:
        self.update_count = 0

    def update(self) -> None:
        self.update_count += 1


def _make_editor(initial_code: str = "") -> tuple[RichCodeEditor, FakePage]:
    page = FakePage()
    return RichCodeEditor(page, get_preset("midnight_dark"), initial_code), page


# -- tokenize() ----------------------------------------------------------------
def test_tokenize_empty_code_returns_a_single_empty_span():
    spans = tokenize("")
    assert len(spans) == 1
    assert spans[0].text == ""


def test_tokenize_colors_keywords_builtins_numbers_strings_and_comments():
    code = 'if x == 1:\n    print("hi")  # done'
    spans = tokenize(code)
    colored = {s.text: s.style.color for s in spans if s.style}
    assert colored["if"] == "#4F8FF7"
    assert colored["print"] == "#A05FD9"
    assert colored["1"] == "#C1791B"
    assert colored['"hi"'] == "#3FA66B"
    assert colored["# done"] == "#9AA0A6"


def test_tokenize_string_wins_over_keyword_when_overlapping():
    # "if" appears inside a string literal -- should render as a string,
    # not a keyword, since TOKEN_PATTERNS applies string after keyword.
    spans = tokenize('x = "if"')
    joined = "".join(s.text for s in spans)
    assert joined == 'x = "if"'
    string_span = next(s for s in spans if s.text == '"if"')
    assert string_span.style.color == "#3FA66B"


def test_tokenize_highlights_only_the_given_error_line():
    code = "a = 1\nb = 2\nc = 3"
    spans = tokenize(code, error_line=2)
    highlighted = {s.text for s in spans if s.style and s.style.bgcolor}
    assert "b" in highlighted or "2" in highlighted
    assert "a" not in highlighted
    assert "1" not in highlighted
    assert "3" not in highlighted


def test_tokenize_no_error_line_has_no_background():
    spans = tokenize("a = 1\nb = 2")
    assert all(s.style is None or s.style.bgcolor is None for s in spans)


# -- RichCodeEditor: value / selection surface --------------------------------
def test_initial_value_matches_starter_code():
    editor, _page = _make_editor('print("Hello!")')
    assert editor.value == 'print("Hello!")'


def test_setting_value_updates_field_and_rebuilds_underlay():
    editor, _page = _make_editor("a = 1")
    editor.value = "b = 2"
    assert editor.value == "b = 2"
    assert "".join(s.text for s in editor._underlay.spans) == "b = 2"


def test_value_defaults_to_empty_string_not_none():
    editor, _page = _make_editor("")
    editor._field.value = None
    assert editor.value == ""


def test_selection_get_set_proxies_the_real_field():
    editor, _page = _make_editor("abcdef")
    editor.selection = ft.TextSelection(base_offset=2, extent_offset=4)
    assert editor.selection.start == 2
    assert editor.selection.end == 4


# -- error line highlight -------------------------------------------------------
def test_highlight_error_line_adds_background_to_that_line_only():
    editor, _page = _make_editor("a = 1\nb = 2")
    editor.highlight_error_line(2)
    highlighted = {s.text for s in editor._underlay.spans if s.style and s.style.bgcolor}
    assert highlighted
    assert "a" not in highlighted


def test_clear_error_highlight_removes_the_background():
    editor, _page = _make_editor("a = 1\nb = 2")
    editor.highlight_error_line(2)
    editor.clear_error_highlight()
    assert all(s.style is None or s.style.bgcolor is None for s in editor._underlay.spans)


def test_setting_value_preserves_the_active_error_highlight():
    editor, _page = _make_editor("a = 1\nb = 2")
    editor.highlight_error_line(1)
    editor.value = "x = 9\nb = 2"
    highlighted = {s.text for s in editor._underlay.spans if s.style and s.style.bgcolor}
    assert "x" in highlighted or "9" in highlighted


# -- on_selection_change chaining (shared with build_macro_toolbar) -----------
def test_on_selection_change_setter_does_not_replace_the_internal_handler():
    editor, _page = _make_editor("print(1)")
    seen = []
    editor.on_selection_change = lambda e: seen.append(e)

    event = ft.TextSelectionChangeEvent(
        name="selection_change", control=editor._field, selected_text="",
        selection=ft.TextSelection(base_offset=3, extent_offset=3),
    )
    editor._field.on_selection_change(event)

    assert seen == [event]
    assert editor._cursor_pos == 3


def test_selection_change_updates_cursor_pos_even_without_external_handler():
    editor, _page = _make_editor("print(1)")
    event = ft.TextSelectionChangeEvent(
        name="selection_change", control=editor._field, selected_text="",
        selection=ft.TextSelection(base_offset=5, extent_offset=5),
    )
    editor._field.on_selection_change(event)
    assert editor._cursor_pos == 5


# -- autocomplete suggestions ---------------------------------------------------
def test_typing_a_prefix_suggests_matching_keywords_and_builtins():
    editor, _page = _make_editor("pri")
    editor._cursor_pos = 3
    editor._rebuild_suggestions()
    labels = [b.content for b in editor._suggestion_row.controls]
    assert "print" in labels


def test_no_word_at_cursor_clears_suggestions():
    editor, _page = _make_editor("print(1) ")
    editor._cursor_pos = len("print(1) ")
    editor._rebuild_suggestions()
    assert editor._suggestion_row.controls == []


def test_suggestions_include_identifiers_already_used_in_the_code():
    editor, _page = _make_editor("player_score = 0\nplay")
    editor._cursor_pos = len("player_score = 0\nplay")
    editor._rebuild_suggestions()
    labels = [b.content for b in editor._suggestion_row.controls]
    assert "player_score" in labels


def test_tapping_a_suggestion_replaces_the_typed_prefix():
    editor, page = _make_editor("pri")
    editor._cursor_pos = 3
    editor._rebuild_suggestions()
    button = next(b for b in editor._suggestion_row.controls if b.content == "print")
    button.on_click(None)

    assert editor.value == "print"
    assert editor.selection.start == len("print")
    assert page.update_count >= 1


def test_tapping_a_suggestion_only_replaces_text_before_the_cursor():
    editor, _page = _make_editor("pri(1)")
    editor._cursor_pos = 3
    editor._rebuild_suggestions()
    button = next(b for b in editor._suggestion_row.controls if b.content == "print")
    button.on_click(None)
    assert editor.value == "print(1)"
