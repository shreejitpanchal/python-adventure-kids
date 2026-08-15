import flet as ft
import pytest

from app.ui.components.macro_toolbar_flet import MACROS, Macro, build_macro_toolbar
from app.ui.theme_flet import get_preset


class FakePage:
    def __init__(self):
        self.update_count = 0

    def update(self):
        self.update_count += 1


def _macro_button(toolbar: ft.Row, label: str) -> ft.Button:
    return next(b for b in toolbar.controls if b.content == label)


def test_builds_one_button_per_macro():
    editor = ft.TextField(value="")
    page = FakePage()
    toolbar = build_macro_toolbar(editor, page, get_preset("midnight_dark"))
    assert isinstance(toolbar, ft.Row)
    assert len(toolbar.controls) == len(MACROS)


def test_tapping_print_inserts_at_the_end_when_no_cursor_tracked_yet():
    editor = ft.TextField(value="x = 1\n")
    page = FakePage()
    toolbar = build_macro_toolbar(editor, page, get_preset("midnight_dark"))

    btn = _macro_button(toolbar, "print()")
    btn.on_click(None)

    assert editor.value == "x = 1\nprint()"
    assert editor.selection.start == editor.selection.end == len("x = 1\nprint(")
    assert page.update_count == 1


def test_tapping_print_inserts_at_the_tracked_cursor_position():
    editor = ft.TextField(value="ab")
    page = FakePage()
    toolbar = build_macro_toolbar(editor, page, get_preset("midnight_dark"))

    # Simulate the client reporting the caret landed between "a" and "b".
    editor.on_selection_change(ft.TextSelectionChangeEvent(
        control=editor, name="selection_change",
        selected_text="", selection=ft.TextSelection(base_offset=1, extent_offset=1),
    ))

    btn = _macro_button(toolbar, "print()")
    btn.on_click(None)

    assert editor.value == "aprint()b"
    assert editor.selection.start == editor.selection.end == len("aprint(")


def test_def_macro_selects_the_placeholder_function_name():
    editor = ft.TextField(value="")
    page = FakePage()
    toolbar = build_macro_toolbar(editor, page, get_preset("midnight_dark"))

    btn = _macro_button(toolbar, "def")
    btn.on_click(None)

    assert editor.value == "def my_function():"
    selected = editor.value[editor.selection.start:editor.selection.end]
    assert selected == "my_function"


def test_second_tap_inserts_after_the_first_inserted_macro():
    editor = ft.TextField(value="")
    page = FakePage()
    toolbar = build_macro_toolbar(editor, page, get_preset("midnight_dark"))

    _macro_button(toolbar, "#").on_click(None)
    _macro_button(toolbar, "print()").on_click(None)

    assert editor.value == "# print()"


@pytest.mark.parametrize("macro", MACROS)
def test_every_macro_lands_its_caret_inside_the_inserted_text(macro: Macro):
    assert 0 <= macro.selection_start <= len(macro.insert_text)
    assert 0 <= macro.selection_end <= len(macro.insert_text)
    assert macro.selection_start <= macro.selection_end
