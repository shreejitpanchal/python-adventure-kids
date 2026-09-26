"""Exercises build_learning_hub_view(): the six world-tile cards, the resume
banner, preferred-mode-first ordering, and the game-world additions (HUD
strip, Daily Treasure chest, once-a-day welcome banner, Codey) -- with a
real AppState/LessonEngine so compute_hub_status() is exercised for real,
not mocked. Controls are found by their data["kind"] role, see
tests/flet_testing.py."""
from __future__ import annotations

import pytest

from app.engine.hub_status import compute_hub_status
from app.progress.store import PlayToday
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.learning_hub_flet import build_learning_hub_view, codey_hub_line
from tests.flet_testing import FakePage, NoTaskPage, all_of, one, texts

_CARD_TITLES = {
    "guided": "Start Learning Python",
    "code_crackers": "Fix Code Cracker Puzzles",
    "advanced_code_crackers": "Advanced Code Crackers",
    "projects": "Build a Project",
    "course": "Python Learning",
    "ai_course": "AI & Machine Learning",
}

_CARD_ROUTES = {
    "guided": "/dashboard",
    "code_crackers": "/categories/code_crackers",
    "advanced_code_crackers": "/categories/advanced_code_crackers",
    "projects": "/projects",
    "course": "/course",
    "ai_course": "/ai-course",
}


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _cards(view) -> list:
    return all_of(view, "hub_card")


# -- the six world tiles ---------------------------------------------------------
def test_all_six_cards_present_with_correct_status_text(state):
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    view = build_learning_hub_view(FakePage(), state)

    cards = _cards(view)
    assert {c.data["title"] for c in cards} == set(_CARD_TITLES.values())

    status_by_key = {c.data["key"]: c.data["status"] for c in cards}
    assert status_by_key["guided"] == hub_status.guided_status
    assert status_by_key["code_crackers"] == hub_status.cracker_status
    assert status_by_key["advanced_code_crackers"] == hub_status.advanced_cracker_status
    assert status_by_key["projects"] == hub_status.project_status
    assert status_by_key["course"] == hub_status.course_status
    assert status_by_key["ai_course"] == hub_status.ai_course_status
    # The status is really rendered, not just tagged.
    for card in cards:
        assert card.data["status"] in texts(card)
        assert card.data["title"] in texts(card)


@pytest.mark.parametrize("key", list(_CARD_TITLES.keys()))
def test_card_click_sets_last_learning_route_and_navigates(state, key):
    page = FakePage()
    view = build_learning_hub_view(page, state)
    card = next(c for c in _cards(view) if c.data["key"] == key)

    card.on_click(None)

    assert state.settings.last_learning_route == key
    assert page.routes_visited == [_CARD_ROUTES[key]]


def test_resume_banner_absent_when_last_learning_route_is_empty(state):
    state.settings.last_learning_route = ""
    view = build_learning_hub_view(FakePage(), state)
    assert all_of(view, "resume_banner") == []


@pytest.mark.parametrize("key", list(_CARD_TITLES.keys()))
def test_resume_banner_present_and_navigates_for_each_valid_key(state, key):
    state.settings.last_learning_route = key
    page = FakePage()
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    view = build_learning_hub_view(page, state)

    banner = one(view, "resume_banner")
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
def test_preferred_mode_renders_first_and_featured(state, mode, expected_first):
    # "crackers"/"advanced" (Settings.preferred_learning_mode's semantic
    # keys) map onto the Hub's own "code_crackers"/"advanced_code_crackers"
    # card keys -- there is no dedicated "crackers" card.
    state.settings.preferred_learning_mode = mode
    view = build_learning_hub_view(FakePage(), state)
    cards = _cards(view)
    assert cards[0].data["key"] == expected_first
    assert cards[0].data["featured"] is True
    assert all(c.data["featured"] is False for c in cards[1:])


def test_default_settings_puts_start_learning_python_first(state):
    assert state.settings.preferred_learning_mode == ""
    view = build_learning_hub_view(FakePage(), state)
    assert _cards(view)[0].data["key"] == "guided"


# -- header, HUD strip, Codey ----------------------------------------------------------
def test_hero_header_and_codey_companion_are_present(state):
    view = build_learning_hub_view(FakePage(), state)
    assert one(view, "hero_header").data["title"] == "Python Adventure"
    companion = one(view, "codey_companion")
    assert codey_hub_line("Explorer", 0, False, True) in texts(companion)


def test_hud_strip_shows_streak_level_xp_stars_and_badges(state):
    view = build_learning_hub_view(FakePage(), state)
    assert one(view, "streak_chip").data["days"] == 0
    assert one(view, "level_chip").data["label"] == "Lv 1 · Curious Coder"
    assert one(view, "xp_chip").data["label"] == "0/100 XP"
    labels = {chip.data["label"] for chip in all_of(view, "stat_chip")}
    assert "0 stars" in labels and "0 badges" in labels


def test_shield_chip_appears_only_once_a_shield_is_held(state, monkeypatch):
    import app.progress.store as store_module
    from datetime import datetime, timezone

    assert all_of(build_learning_hub_view(FakePage(), state), "shield_chip") == []

    for day in range(1, 8):  # seven straight days earns a shield
        class Frozen(datetime):
            @classmethod
            def now(cls, tz=None, _day=day):
                return datetime(2026, 9, _day, 12, tzinfo=timezone.utc)

        monkeypatch.setattr(store_module, "datetime", Frozen)
        state.progress.record_play_today()

    view = build_learning_hub_view(FakePage(), state)
    assert one(view, "shield_chip").data["shields"] == 1


def test_quest_board_is_on_the_hub_with_three_quests(state):
    view = build_learning_hub_view(FakePage(), state)
    board = one(view, "quest_board")
    assert board.data["total"] == 3 and board.data["done"] == 0
    assert len(all_of(board, "quest_row")) == 3


def test_codey_nudges_to_claim_a_finished_quest_board(state):
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.complete_lesson("lesson_02", 3)
    state.progress.open_daily_chest()
    state.progress.record_quiz_attempt(5, 10)
    view = build_learning_hub_view(FakePage(), state)
    assert one(view, "quest_board").data["claimable"] is True
    assert codey_hub_line("Explorer", 0, False, False, quests_ready=True) in texts(one(view, "codey_companion"))


def test_codey_wears_no_accessory_at_level_one_and_a_cap_as_a_bug_hunter(state):
    view = build_learning_hub_view(FakePage(), state)
    assert one(view, "codey_accessory").visible is False

    state.progress.add_xp(100 + 200)  # level 3
    view = build_learning_hub_view(FakePage(), state)
    accessory = one(view, "codey_accessory")
    assert accessory.visible is True and accessory.data["accessory"] == "🧢"
    assert one(view, "level_chip").data["label"] == "Lv 3 · Bug Hunter"


# -- responsive layout ------------------------------------------------------------------
def test_compact_layout_stacks_full_width_cards(state):
    view = build_learning_hub_view(FakePage(), state)
    assert all_of(view, "card_grid") == []
    assert all_of(view, "content_column") == []
    assert all(card.width is None for card in _cards(view))


def test_wide_layout_caps_content_and_lays_cards_out_in_a_wrapping_grid(state):
    page = FakePage()
    page.width = 1200
    view = build_learning_hub_view(page, state)
    assert one(view, "content_column").width == 880
    grid = one(view, "card_grid")
    assert grid.wrap is True
    assert len(_cards(grid)) == 6
    assert all(card.width == 340 for card in _cards(view))


def test_codey_hub_line_prioritises_quests_then_chest_then_resume_then_streak():
    assert "claim your bonus" in codey_hub_line("Sam", 5, True, True, quests_ready=True)
    assert "treasure" in codey_hub_line("Sam", 0, False, True).lower()
    assert "3 days in a row, Sam" in codey_hub_line("Sam", 3, True, True)
    assert codey_hub_line("Sam", 0, True, False) == "Want to pick up where you left off?"
    assert "5 days in a row" in codey_hub_line("Sam", 5, False, False)
    assert "Sam" in codey_hub_line("Sam", 1, False, False)


# -- daily treasure chest ----------------------------------------------------------------
def test_daily_chest_opens_once_grants_xp_and_updates_the_hud(state):
    page = FakePage()
    view = build_learning_hub_view(page, state)
    chest = one(view, "daily_chest")
    assert chest.data["opened"] is False
    assert chest.on_click is not None

    chest.on_click(None)

    assert chest.data["opened"] is True
    assert chest.data["reward_xp"] > 0
    assert state.progress.can_open_daily_chest() is False
    assert state.progress.get_player_level().total_xp == chest.data["reward_xp"]
    assert f"+{chest.data['reward_xp']} XP!" in texts(chest)
    assert one(view, "xp_chip").data["label"] == "0/100 XP"  # data is build-time; the live text updated:
    assert one(view, "xp_chip").content.controls[1].value == (
        f"{state.progress.get_player_level().xp_into_level}/{state.progress.get_player_level().xp_needed_for_level} XP"
    )
    assert chest.on_click is None, "a second tap must do nothing"


def test_daily_chest_shows_collected_state_when_already_opened_today(state):
    state.progress.open_daily_chest()
    view = build_learning_hub_view(FakePage(), state)
    chest = one(view, "daily_chest")
    assert chest.data["opened"] is True
    assert chest.on_click is None
    assert "Come back tomorrow" in " ".join(texts(chest))


# -- welcome-back moment ----------------------------------------------------------------
def test_welcome_banner_shows_once_per_launch_day_then_is_consumed(state):
    state.settings.child_name = "Kidoo"
    state.welcome = PlayToday(first_play_today=True, streak_days=3, streak_continued=True, streak_reset=False)

    first_view = build_learning_hub_view(FakePage(), state)
    banner = one(first_view, "welcome_banner")
    assert "Day 3 streak, Kidoo" in banner.data["message"]
    assert state.welcome is None

    second_view = build_learning_hub_view(FakePage(), state)
    assert all_of(second_view, "welcome_banner") == []


def test_no_welcome_banner_without_a_first_play_today(state):
    assert state.welcome is None
    assert all_of(build_learning_hub_view(FakePage(), state), "welcome_banner") == []

    state.welcome = PlayToday(first_play_today=False, streak_days=4, streak_continued=False, streak_reset=False)
    assert all_of(build_learning_hub_view(FakePage(), state), "welcome_banner") == []


# -- motion ---------------------------------------------------------------------------------
def test_sections_start_hidden_and_a_staggered_reveal_is_scheduled(state):
    page = FakePage()
    view = build_learning_hub_view(page, state)
    assert all(c.opacity == 0.0 for c in _cards(view))
    assert len(page.scheduled(motion._reveal_staggered)) == 1


def test_sections_are_revealed_immediately_when_the_page_cannot_animate(state):
    view = build_learning_hub_view(NoTaskPage(), state)
    assert all(c.opacity == 1.0 for c in _cards(view))
    assert one(view, "daily_chest").opacity == 1.0
