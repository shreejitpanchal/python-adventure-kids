import pytest

from app.engine.quests import QUEST_BONUS_XP, daily_quests
from app.progress.store import today_iso
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.components.quest_board_flet import CLAIMED_TEXT, build_quest_board
from tests.flet_testing import FakePage, all_of, one, texts


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _do_everything(state) -> None:
    """Satisfies every quest in the pool, whichever three today picked."""
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.complete_lesson("lesson_02", 3)
    state.progress.open_daily_chest()
    state.progress.record_quiz_attempt(5, 10)


def test_fresh_board_lists_todays_three_quests_unfinished(state):
    board = build_quest_board(FakePage(), state, scale=1.0)
    assert board.data["done"] == 0 and board.data["total"] == 3
    assert board.data["claimable"] is False and board.data["claimed"] is False
    rows = all_of(board, "quest_row")
    assert [row.data["quest_id"] for row in rows] == [q.id for q in daily_quests(today_iso())]
    assert all(row.data["done"] is False for row in rows)
    assert any(f"+{QUEST_BONUS_XP} XP" in t for t in texts(board))
    assert all_of(board, "game_button") == []


def test_finished_board_offers_the_bonus_and_claims_it_once(state):
    _do_everything(state)
    xp_before = state.progress.get_player_level().total_xp
    page = FakePage()
    claimed_levels = []
    board = build_quest_board(page, state, scale=1.0, on_bonus_claimed=claimed_levels.append)

    assert board.data["done"] == 3 and board.data["claimable"] is True
    assert all(row.data["done"] for row in all_of(board, "quest_row"))
    button = one(board, "game_button")
    assert f"+{QUEST_BONUS_XP} XP" in button.data["text"]

    # The GestureDetector wraps the chunky container; its on_tap is the claim.
    gesture = one(board, "quest_footer").content.controls[0]
    gesture.on_tap(None)

    assert state.progress.get_player_level().total_xp == xp_before + QUEST_BONUS_XP
    assert state.progress.can_claim_quest_bonus() is False
    assert len(claimed_levels) == 1
    assert board.data["claimed"] is True and board.data["claimable"] is False
    assert CLAIMED_TEXT in texts(board)
    assert len(page.scheduled(motion._pulse)) >= 1


def test_already_claimed_board_shows_the_claimed_state(state):
    _do_everything(state)
    state.progress.claim_quest_bonus(QUEST_BONUS_XP)
    board = build_quest_board(FakePage(), state, scale=1.0)
    assert board.data["claimed"] is True and board.data["claimable"] is False
    assert CLAIMED_TEXT in texts(board)
    assert all_of(board, "game_button") == []
