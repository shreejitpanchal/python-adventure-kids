"""Exercises build_learning_hub_view()'s five cards, the resume banner, and
the preferred-mode-first ordering -- with a real AppState/LessonEngine
(so compute_hub_status() is exercised for real, not mocked), same pattern
as test_dashboard_flet.py."""
from __future__ import annotations

import flet as ft
import pytest

from app.engine.hub_status import compute_hub_status
from app.ui.app_state_flet import AppState
from app.ui.learning_hub_flet import build_learning_hub_view

_CARD_TITLES = {
    "guided": "🚀 Start Learning Python",
    "code_crackers": "🐛 Fix Code Cracker Puzzles",
    "advanced_code_crackers": "🧠 Advanced Code Crackers",
    "projects": "🛠️ Build a Project",
    "course": "🎓 Python Learning",
}

_CARD_ROUTES = {
    "guided": "/dashboard",
    "code_crackers": "/categories/code_crackers",
    "advanced_code_crackers": "/categories/advanced_code_crackers",
    "projects": "/projects",
    "course": "/course",
}


class FakePage:
    def __init__(self) -> None:
        self.routes_visited: list[str] = []

    def update(self) -> None:
        pass

    def go(self, route: str) -> None:
        self.routes_visited.append(route)


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _cards(view: ft.View) -> list[ft.Container]:
    """Every card container -- content is a Column (title/subtitle/status),
    distinguishing it from the resume banner (content is a bare Text)."""
    return [
        c for c in view.controls
        if isinstance(c, ft.Container) and isinstance(getattr(c, "content", None), ft.Column)
    ]


def _resume_banner(view: ft.View) -> ft.Container | None:
    for c in view.controls:
        if isinstance(c, ft.Container) and isinstance(getattr(c, "content", None), ft.Text):
            return c
    return None


def _card_title(card: ft.Container) -> str:
    return card.content.controls[0].value


def _card_status(card: ft.Container) -> str:
    return card.content.controls[2].value


def test_all_five_cards_present_with_correct_status_text(state):
    page = FakePage()
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    view = build_learning_hub_view(page, state)

    cards = _cards(view)
    titles = {_card_title(c) for c in cards}
    assert titles == set(_CARD_TITLES.values())

    status_by_title = {_card_title(c): _card_status(c) for c in cards}
    assert status_by_title[_CARD_TITLES["guided"]] == hub_status.guided_status
    assert status_by_title[_CARD_TITLES["code_crackers"]] == hub_status.cracker_status
    assert status_by_title[_CARD_TITLES["advanced_code_crackers"]] == hub_status.advanced_cracker_status
    assert status_by_title[_CARD_TITLES["projects"]] == hub_status.project_status
    assert status_by_title[_CARD_TITLES["course"]] == hub_status.course_status


@pytest.mark.parametrize("key", list(_CARD_TITLES.keys()))
def test_card_click_sets_last_learning_route_and_navigates(state, key):
    page = FakePage()
    view = build_learning_hub_view(page, state)
    cards = _cards(view)
    card = next(c for c in cards if _card_title(c) == _CARD_TITLES[key])

    card.on_click(None)

    assert state.settings.last_learning_route == key
    assert page.routes_visited == [_CARD_ROUTES[key]]


def test_resume_banner_absent_when_last_learning_route_is_empty(state):
    state.settings.last_learning_route = ""
    page = FakePage()
    view = build_learning_hub_view(page, state)
    assert _resume_banner(view) is None


@pytest.mark.parametrize("key", list(_CARD_TITLES.keys()))
def test_resume_banner_present_and_navigates_for_each_valid_key(state, key):
    state.settings.last_learning_route = key
    page = FakePage()
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    view = build_learning_hub_view(page, state)

    banner = _resume_banner(view)
    assert banner is not None
    assert hub_status.resume_label in banner.content.value

    banner.on_click(None)
    assert page.routes_visited == [_CARD_ROUTES[key]]


@pytest.mark.parametrize("mode,expected_first", [
    ("", "guided"),
    ("guided", "guided"),
    ("projects", "projects"),
    ("crackers", "code_crackers"),
    ("advanced", "advanced_code_crackers"),
])
def test_preferred_mode_renders_first(state, mode, expected_first):
    # "crackers"/"advanced" (Settings.preferred_learning_mode's semantic
    # keys) map onto the Hub's own "code_crackers"/"advanced_code_crackers"
    # card keys -- there is no dedicated "crackers" card, only the two
    # existing Code Cracker cards, so the spec's `preferred_learning_mode`
    # value that names a mode is treated as picking the matching card here.
    state.settings.preferred_learning_mode = mode
    page = FakePage()
    view = build_learning_hub_view(page, state)
    cards = _cards(view)
    assert _card_title(cards[0]) == _CARD_TITLES[expected_first]


def test_default_settings_puts_start_learning_python_first(state):
    assert state.settings.preferred_learning_mode == ""
    page = FakePage()
    view = build_learning_hub_view(page, state)
    cards = _cards(view)
    assert _card_title(cards[0]) == _CARD_TITLES["guided"]
