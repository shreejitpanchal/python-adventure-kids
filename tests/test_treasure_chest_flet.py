import pytest

from app.progress.store import ChestReward, PlayerLevel
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.components.treasure_chest_flet import (
    CLOSED_SUBTITLE, CLOSED_TITLE, OPEN_EMOJI, OPENED_SUBTITLE, build_daily_chest, reward_lines,
)
from tests.flet_testing import FakePage, NoTaskPage, texts


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _level(level: int) -> PlayerLevel:
    return PlayerLevel(level=level, xp_into_level=0, xp_needed_for_level=level * 100, total_xp=0)


def test_reward_lines():
    assert reward_lines(ChestReward(xp=20, streak_bonus_xp=0, level=_level(1), leveled_up=False)) == (
        "+20 XP!", "Keep your streak going for a bonus tomorrow!",
    )
    assert reward_lines(ChestReward(xp=20, streak_bonus_xp=10, level=_level(1), leveled_up=False)) == (
        "+30 XP!", "20 XP + 10 streak bonus",
    )
    assert "Level 2" in reward_lines(ChestReward(xp=20, streak_bonus_xp=0, level=_level(2), leveled_up=True))[1]


def test_closed_chest_renders_tap_prompt_and_pulses(state):
    page = FakePage()
    card = build_daily_chest(page, state, scale=1.0)
    assert card.data == {"kind": "daily_chest", "opened": False}
    assert CLOSED_TITLE in texts(card) and CLOSED_SUBTITLE in texts(card)
    assert card.on_click is not None and card.ink is True
    assert len(page.scheduled(motion._pulse)) == 1


def test_opening_grants_xp_updates_the_card_and_notifies(state):
    page = FakePage()
    rewards = []
    card = build_daily_chest(page, state, scale=1.0, on_opened=rewards.append)

    card.on_click(None)

    assert len(rewards) == 1
    reward = rewards[0]
    assert reward.total_xp > 0
    assert state.progress.get_player_level().total_xp == reward.total_xp
    assert card.data["opened"] is True and card.data["reward_xp"] == reward.total_xp
    assert f"+{reward.total_xp} XP!" in texts(card)
    assert OPEN_EMOJI in texts(card)
    assert card.on_click is None and card.ink is False
    assert page.update_count >= 1
    assert len(page.scheduled(motion._wobble)) == 1


def test_already_opened_today_renders_the_collected_state(state):
    state.progress.open_daily_chest()
    card = build_daily_chest(NoTaskPage(), state, scale=1.0)
    assert card.data["opened"] is True
    assert card.on_click is None
    assert OPENED_SUBTITLE in texts(card)


def test_a_racing_second_open_settles_without_granting_twice(state):
    page = FakePage()
    rewards = []
    card = build_daily_chest(page, state, scale=1.0, on_opened=rewards.append)
    handler = card.on_click
    handler(None)
    handler(None)  # the closure still exists even though the card's on_click was cleared
    assert len(rewards) == 1
    assert state.progress.get_player_level().total_xp == rewards[0].total_xp
    assert OPENED_SUBTITLE in texts(card)
