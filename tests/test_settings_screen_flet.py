"""Exercises settings_screen_flet.py's "💾 Progress" card -- export/import
handlers driven via fake ft.FilePicker/ft.Share classes (real OS file
dialogs and native share sheets can't be automated in a test), same
async-handler-invoked-via-asyncio.run() pattern as
test_lesson_screen_flet.py's _on_run().

ft.FilePicker()/ft.Share() are constructed fresh inside each handler (see
_build_progress_card()'s docstring for why), so the fakes are installed by
monkeypatching the class itself in app.ui.settings_screen_flet's `ft`
namespace to a factory returning one shared, pre-configured fake instance
per test -- the handlers don't care that every "fresh" FilePicker() call
returns the same object, only that it behaves like one.
"""
from __future__ import annotations

import asyncio
import json

import flet as ft
import pytest

import app.ui.settings_screen_flet as settings_flet
from app.progress.store import PROGRESS_EXPORT_FORMAT_VERSION, ProgressStore
from app.ui.app_state_flet import AppState
from app.ui.settings_screen_flet import build_settings_view


class FakeFilePickerFile:
    def __init__(self, data: bytes) -> None:
        self.bytes = data


class FakeFilePicker:
    def __init__(self) -> None:
        self.save_result: str | None = None
        self.pick_result: list = []
        self.save_calls: list[dict] = []
        self.pick_calls: list[dict] = []
        self.raise_on_save: Exception | None = None
        self.raise_on_pick: Exception | None = None

    async def save_file(self, **kwargs):
        self.save_calls.append(kwargs)
        if self.raise_on_save:
            raise self.raise_on_save
        return self.save_result

    async def pick_files(self, **kwargs):
        self.pick_calls.append(kwargs)
        if self.raise_on_pick:
            raise self.raise_on_pick
        return self.pick_result


class FakeShareResult:
    def __init__(self, status) -> None:
        self.status = status


class FakeShare:
    def __init__(self) -> None:
        self.share_files_calls: list = []
        self.result_status = ft.ShareResultStatus.SUCCESS
        self.raise_on_share: Exception | None = None

    async def share_files(self, files, **kwargs):
        self.share_files_calls.append((files, kwargs))
        if self.raise_on_share:
            raise self.raise_on_share
        return FakeShareResult(self.result_status)


class FakePage:
    def __init__(self, platform=ft.PagePlatform.WINDOWS) -> None:
        self.dialogs: list = []
        self.platform = platform

    def update(self) -> None:
        pass

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        if self.dialogs:
            self.dialogs.pop()

    def run_task(self, fn, *args) -> None:
        # Real Flet schedules this onto the page's event loop; tests just
        # need the side effects to happen deterministically, so run it now.
        asyncio.run(fn(*args))


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


@pytest.fixture
def fake_picker(monkeypatch):
    picker = FakeFilePicker()
    monkeypatch.setattr(settings_flet.ft, "FilePicker", lambda: picker)
    return picker


@pytest.fixture
def fake_share(monkeypatch):
    share = FakeShare()
    monkeypatch.setattr(settings_flet.ft, "Share", lambda: share)
    return share


def _progress_card(view):
    # controls = [header, sound_card, font_card, theme_card, progress_card, version_row, spacer]
    return view.controls[4]


def _status_text(view):
    return _progress_card(view).content.controls[-1]


def _export_button(view):
    return _progress_card(view).content.controls[2].controls[0]


def _import_button(view):
    return _progress_card(view).content.controls[2].controls[1]


# -- export: desktop (direct save, no share choice) ------------------------
def test_desktop_export_saves_directly_without_a_choice_dialog(state, fake_picker):
    fake_picker.save_result = "/tmp/out.json"
    state.progress.complete_lesson("lesson_01", 3)

    page = FakePage(platform=ft.PagePlatform.WINDOWS)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    assert page.dialogs == []
    assert len(fake_picker.save_calls) == 1
    payload = fake_picker.save_calls[0]["src_bytes"]
    data = json.loads(payload.decode("utf-8"))
    assert data["format_version"] == PROGRESS_EXPORT_FORMAT_VERSION
    assert data["lesson_completions"][0]["lesson_id"] == "lesson_01"
    assert "Saved to /tmp/out.json" in _status_text(view).value


def test_desktop_export_cancelled_reports_cancellation(state, fake_picker):
    fake_picker.save_result = None
    page = FakePage(platform=ft.PagePlatform.WINDOWS)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    assert "cancelled" in _status_text(view).value.lower()


def test_desktop_export_failure_shows_error(state, fake_picker):
    fake_picker.raise_on_save = RuntimeError("disk full")
    page = FakePage(platform=ft.PagePlatform.WINDOWS)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    assert "failed" in _status_text(view).value.lower()


# -- export: mobile (Save to Device / Share / Cancel choice) ---------------
def test_mobile_export_shows_save_share_cancel_choice(state, fake_picker, fake_share):
    page = FakePage(platform=ft.PagePlatform.ANDROID)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    button_texts = [b.content if isinstance(b.content, str) else b.text for b in dialog.actions]
    assert any("Save" in str(t) for t in button_texts)
    assert any("Share" in str(t) for t in button_texts)
    assert any("Cancel" in str(t) for t in button_texts)
    # Neither action has actually run yet.
    assert fake_picker.save_calls == []
    assert fake_share.share_files_calls == []


def test_mobile_export_choosing_save_calls_the_file_picker(state, fake_picker, fake_share):
    fake_picker.save_result = "/storage/out.json"
    page = FakePage(platform=ft.PagePlatform.ANDROID)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    dialog = page.dialogs[0]
    save_button = next(b for b in dialog.actions if "Save" in str(b.content))
    save_button.on_click(None)

    assert page.dialogs == []
    assert len(fake_picker.save_calls) == 1
    assert "Saved to /storage/out.json" in _status_text(view).value


def test_mobile_export_choosing_share_calls_the_share_service(state, fake_picker, fake_share):
    page = FakePage(platform=ft.PagePlatform.ANDROID)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    dialog = page.dialogs[0]
    share_button = next(b for b in dialog.actions if "Share" in str(b.content))
    share_button.on_click(None)

    assert page.dialogs == []
    assert len(fake_share.share_files_calls) == 1
    assert "Shared" in _status_text(view).value


def test_mobile_export_choosing_cancel_does_nothing(state, fake_picker, fake_share):
    page = FakePage(platform=ft.PagePlatform.ANDROID)
    view = build_settings_view(page, state)
    asyncio.run(_export_button(view).on_click(None))

    dialog = page.dialogs[0]
    cancel_button = next(b for b in dialog.actions if "Cancel" in str(b.content))
    cancel_button.on_click(None)

    assert page.dialogs == []
    assert fake_picker.save_calls == []
    assert fake_share.share_files_calls == []


# -- import ------------------------------------------------------------------
def test_import_shows_confirm_dialog_without_overwriting_yet(state, fake_picker):
    exported = json.dumps(state.progress.export_progress_data()).encode("utf-8")
    fake_picker.pick_result = [FakeFilePickerFile(exported)]
    state.progress.complete_lesson("lesson_existing", 2)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    assert len(page.dialogs) == 1
    assert fake_picker.pick_calls[0]["with_data"] is True
    # Not overwritten yet -- only the confirm dialog is shown so far.
    assert state.progress.get_completed_lesson_ids() == ["lesson_existing"]


def test_import_confirm_overwrites_progress(state, fake_picker, tmp_path):
    src_store = ProgressStore(tmp_path / "src.sqlite3")
    src_store.complete_lesson("lesson_a", 3)
    src_store.complete_lesson("lesson_b", 3)
    exported = json.dumps(src_store.export_progress_data()).encode("utf-8")
    src_store.close()

    fake_picker.pick_result = [FakeFilePickerFile(exported)]
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


def test_import_cancel_does_not_overwrite(state, fake_picker):
    exported = json.dumps(state.progress.export_progress_data()).encode("utf-8")
    fake_picker.pick_result = [FakeFilePickerFile(exported)]
    state.progress.complete_lesson("lesson_existing", 2)

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    dialog = page.dialogs[0]
    cancel_button = dialog.actions[0]
    cancel_button.on_click(None)

    assert state.progress.get_completed_lesson_ids() == ["lesson_existing"]
    assert page.dialogs == []


def test_import_rejects_invalid_file_with_status_message(state, fake_picker):
    bad = json.dumps({"not": "a real export"}).encode("utf-8")
    fake_picker.pick_result = [FakeFilePickerFile(bad)]

    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    dialog = page.dialogs[0]
    confirm_button = dialog.actions[1]
    confirm_button.on_click(None)

    assert "doesn't look like" in _status_text(view).value


def test_import_cancelled_file_pick_does_nothing(state, fake_picker):
    fake_picker.pick_result = []
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    assert page.dialogs == []
    assert _status_text(view).value == ""


def test_import_unreadable_file_shows_error(state, fake_picker):
    fake_picker.pick_result = [FakeFilePickerFile(b"not valid json")]
    page = FakePage()
    view = build_settings_view(page, state)
    asyncio.run(_import_button(view).on_click(None))

    assert page.dialogs == []
    assert "couldn't read" in _status_text(view).value.lower()
