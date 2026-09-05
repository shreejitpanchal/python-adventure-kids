"""Exercises settings_screen_flet.py's "💾 Progress" card -- export/import
handlers driven via a FakeFilePicker (real OS file dialogs can't be
automated in a test), same async-handler-invoked-via-asyncio.run() pattern
as test_lesson_screen_flet.py's _on_run()."""
from __future__ import annotations

import asyncio
import json

import pytest

from app.progress.store import PROGRESS_EXPORT_FORMAT_VERSION, ProgressStore
from app.ui.app_state_flet import AppState
from app.ui.settings_screen_flet import build_settings_view


class FakeFile:
    def __init__(self, path: str) -> None:
        self.path = path


class FakeFilePicker:
    def __init__(self, save_path=None, pick_paths=None) -> None:
        self.save_path = save_path
        self.pick_paths = pick_paths or []

    async def save_file(self, **kwargs):
        return self.save_path

    async def pick_files(self, **kwargs):
        return [FakeFile(p) for p in self.pick_paths]


class FakePage:
    def __init__(self) -> None:
        self.dialogs: list = []

    def update(self) -> None:
        pass

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        if self.dialogs:
            self.dialogs.pop()


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _progress_card(view):
    # controls = [header, sound_card, font_card, theme_card, progress_card, version_row, spacer]
    return view.controls[4]


def _status_text(view):
    return _progress_card(view).content.controls[-1]


def _export_button(view):
    return _progress_card(view).content.controls[2].controls[0]


def _import_button(view):
    return _progress_card(view).content.controls[2].controls[1]


def test_export_writes_a_json_file(tmp_path, state):
    out_path = str(tmp_path / "out.json")
    state.file_picker = FakeFilePicker(save_path=out_path)
    state.progress.complete_lesson("lesson_01", 3)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    with open(out_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["format_version"] == PROGRESS_EXPORT_FORMAT_VERSION
    assert data["lesson_completions"][0]["lesson_id"] == "lesson_01"
    assert "exported to" in _status_text(view).value


def test_export_appends_json_extension_if_missing(tmp_path, state):
    out_path = str(tmp_path / "out")
    state.file_picker = FakeFilePicker(save_path=out_path)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    assert (tmp_path / "out.json").exists()


def test_export_cancelled_does_nothing(tmp_path, state):
    state.file_picker = FakeFilePicker(save_path=None)
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))
    assert _status_text(view).value == ""


def test_import_shows_confirm_dialog_without_overwriting_yet(tmp_path, state):
    path = tmp_path / "in.json"
    path.write_text(json.dumps(state.progress.export_progress_data()), encoding="utf-8")
    state.file_picker = FakeFilePicker(pick_paths=[str(path)])
    state.progress.complete_lesson("lesson_existing", 2)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    assert len(page.dialogs) == 1
    # Not overwritten yet -- only the confirm dialog is shown so far.
    assert state.progress.get_completed_lesson_ids() == ["lesson_existing"]


def test_import_confirm_overwrites_progress(tmp_path, state):
    src_store = ProgressStore(tmp_path / "src.sqlite3")
    src_store.complete_lesson("lesson_a", 3)
    src_store.complete_lesson("lesson_b", 3)
    exported = src_store.export_progress_data()
    src_store.close()

    path = tmp_path / "in.json"
    path.write_text(json.dumps(exported), encoding="utf-8")
    state.file_picker = FakeFilePicker(pick_paths=[str(path)])
    state.progress.complete_lesson("lesson_existing", 2)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    dialog = page.dialogs[0]
    confirm_button = dialog.actions[1]
    confirm_button.on_click(None)

    assert sorted(state.progress.get_completed_lesson_ids()) == ["lesson_a", "lesson_b"]
    assert page.dialogs == []
    assert "imported successfully" in _status_text(view).value


def test_import_cancel_does_not_overwrite(tmp_path, state):
    path = tmp_path / "in.json"
    path.write_text(json.dumps(state.progress.export_progress_data()), encoding="utf-8")
    state.file_picker = FakeFilePicker(pick_paths=[str(path)])
    state.progress.complete_lesson("lesson_existing", 2)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    dialog = page.dialogs[0]
    cancel_button = dialog.actions[0]
    cancel_button.on_click(None)

    assert state.progress.get_completed_lesson_ids() == ["lesson_existing"]
    assert page.dialogs == []


def test_import_rejects_invalid_file_with_status_message(tmp_path, state):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"not": "a real export"}), encoding="utf-8")
    state.file_picker = FakeFilePicker(pick_paths=[str(path)])

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    dialog = page.dialogs[0]
    confirm_button = dialog.actions[1]
    confirm_button.on_click(None)

    assert "doesn't look like" in _status_text(view).value


def test_import_cancelled_file_pick_does_nothing(tmp_path, state):
    state.file_picker = FakeFilePicker(pick_paths=[])
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    assert page.dialogs == []
    assert _status_text(view).value == ""


# -- state.file_picker is None (its real default -- see AppState.file_picker's
# docstring for why: ft.FilePicker renders as an "Unknown control" banner
# and broke app launch on a real Android device) ---------------------------
def test_buttons_disabled_and_message_shown_when_file_picker_unavailable(state):
    assert state.file_picker is None  # the actual default, not overridden here
    page = FakePage()
    view = build_settings_view(page, state)

    assert _export_button(view).disabled is True
    assert _import_button(view).disabled is True
    assert "isn't available" in _status_text(view).value


def test_export_handler_no_ops_when_file_picker_unavailable(state):
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))
    # Still the same "unavailable" message -- no crash, nothing written.
    assert "isn't available" in _status_text(view).value


def test_import_handler_no_ops_when_file_picker_unavailable(state):
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))
    assert page.dialogs == []
