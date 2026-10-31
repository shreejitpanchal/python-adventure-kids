"""HapticsFlet (app/ui/components/haptics_flet.py): fires the matching
ft.HapticFeedback method through page.run_task, and no-ops -- never
raises -- when the toggle is off, the page can't schedule, or the service
is missing or broken."""
from __future__ import annotations

import pytest

from app.config.settings import Settings
from app.ui.components import haptics_flet
from app.ui.components.haptics_flet import HapticsFlet
from tests.flet_testing import FakePage, NoTaskPage


class FakeService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def light_impact(self) -> None:
        self.calls.append("light")

    async def medium_impact(self) -> None:
        self.calls.append("medium")

    async def heavy_impact(self) -> None:
        self.calls.append("heavy")

    async def vibrate(self) -> None:
        self.calls.append("vibrate")


@pytest.fixture
def service(monkeypatch):
    fake = FakeService()
    monkeypatch.setattr(haptics_flet.ft, "HapticFeedback", lambda: fake, raising=False)
    return fake


def _scheduled_names(page: FakePage) -> list[str]:
    return [handler.__name__ for handler, _args, _kwargs in page.run_task_calls]


def test_each_feel_schedules_its_impact_method(service):
    page = FakePage()
    haptics = HapticsFlet(page)
    settings = Settings()

    assert haptics.tap(settings) and haptics.error(settings) and haptics.success(settings) and haptics.reward(settings)
    assert _scheduled_names(page) == ["light_impact", "medium_impact", "heavy_impact", "vibrate"]


def test_service_is_created_lazily_once_and_only_on_first_use(monkeypatch):
    created: list[FakeService] = []

    def factory():
        fake = FakeService()
        created.append(fake)
        return fake

    monkeypatch.setattr(haptics_flet.ft, "HapticFeedback", factory, raising=False)
    page = FakePage()
    haptics = HapticsFlet(page)
    assert created == [], "constructing HapticsFlet must not touch the page session"
    haptics.tap(Settings())
    haptics.tap(Settings())
    assert len(created) == 1


def test_disabled_in_settings_schedules_nothing(service):
    page = FakePage()
    assert HapticsFlet(page).success(Settings(haptics_enabled=False)) is False
    assert page.run_task_calls == []


def test_degrades_without_run_task_or_without_the_service(monkeypatch):
    assert HapticsFlet(NoTaskPage()).tap(Settings()) is False

    monkeypatch.delattr(haptics_flet.ft, "HapticFeedback", raising=False)
    page = FakePage()
    assert HapticsFlet(page).tap(Settings()) is False
    assert page.run_task_calls == []


def test_a_service_that_fails_to_construct_is_remembered_and_never_retried(monkeypatch):
    attempts = {"count": 0}

    def exploding():
        attempts["count"] += 1
        raise RuntimeError("no session")

    monkeypatch.setattr(haptics_flet.ft, "HapticFeedback", exploding, raising=False)
    haptics = HapticsFlet(FakePage())
    assert haptics.tap(Settings()) is False
    assert haptics.tap(Settings()) is False
    assert attempts["count"] == 1


def test_haptics_enabled_defaults_on_and_round_trips(tmp_path, monkeypatch):
    import app.config.settings as settings_module
    from app.config.settings import load_settings, save_settings

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    assert Settings().haptics_enabled is True
    settings = Settings(haptics_enabled=False)
    save_settings(settings)
    assert load_settings().haptics_enabled is False
