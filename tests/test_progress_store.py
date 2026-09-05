from datetime import datetime, timedelta, timezone

import pytest

import app.progress.store as store_module
from app.progress.store import ProgressStore


@pytest.fixture
def store(tmp_path):
    s = ProgressStore(tmp_path / "progress.sqlite3")
    yield s
    s.close()


def test_new_profile_starts_at_level_one_with_no_stars(store):
    summary = store.get_summary()
    assert summary.level == 1
    assert summary.total_stars == 0
    assert summary.lessons_completed == 0
    assert summary.badges_earned == 0


def test_complete_lesson_updates_stars_and_completion_count(store):
    store.complete_lesson("lesson_01", stars_earned=3)

    summary = store.get_summary()
    assert summary.total_stars == 3
    assert summary.lessons_completed == 1
    assert store.is_lesson_completed("lesson_01") is True
    assert store.is_lesson_completed("lesson_02") is False


def test_get_stars_by_lesson(store):
    store.complete_lesson("lesson_01", stars_earned=3)
    store.complete_lesson("lesson_02", stars_earned=4)

    assert store.get_stars_by_lesson() == {"lesson_01": 3, "lesson_02": 4}


def test_get_stars_by_lesson_empty_when_nothing_completed(store):
    assert store.get_stars_by_lesson() == {}


def test_completing_same_lesson_again_keeps_best_star_count(store):
    store.complete_lesson("lesson_01", stars_earned=1)
    store.complete_lesson("lesson_01", stars_earned=3)
    store.complete_lesson("lesson_01", stars_earned=2)

    summary = store.get_summary()
    assert summary.lessons_completed == 1
    assert summary.total_stars == 3


def test_award_badge_is_idempotent(store):
    assert store.award_badge("first_program") is True
    assert store.award_badge("first_program") is False

    assert store.get_badge_ids() == ["first_program"]
    assert store.get_summary().badges_earned == 1


def test_record_play_today_builds_a_streak(store, monkeypatch):
    import app.progress.store as store_module
    from datetime import datetime, timezone

    monkeypatch.setattr(
        store_module, "_now", lambda: "2026-08-10T00:00:00+00:00"
    )

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 10, tzinfo=timezone.utc)

    monkeypatch.setattr(store_module, "datetime", FixedDatetime)
    store.record_play_today()
    assert store.get_summary().streak_days == 1

    class NextDay(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 11, tzinfo=timezone.utc)

    monkeypatch.setattr(store_module, "datetime", NextDay)
    store.record_play_today()
    assert store.get_summary().streak_days == 2


def test_reset_progress_clears_everything(store):
    store.complete_lesson("lesson_01", stars_earned=3)
    store.award_badge("first_program")
    store.set_level(3)

    store.reset_progress()

    summary = store.get_summary()
    assert summary.level == 1
    assert summary.total_stars == 0
    assert summary.lessons_completed == 0
    assert summary.badges_earned == 0
    assert store.get_completed_lesson_ids() == []


def test_log_event_recorded_in_activity(store):
    store.log_event("lesson_01", "hint_used", "hint #1")

    recent = store.get_recent_activity()
    assert len(recent) == 1
    assert recent[0]["event_type"] == "hint_used"
    assert recent[0]["lesson_id"] == "lesson_01"


def test_best_quiz_score_is_none_when_never_played(store):
    assert store.get_best_quiz_score() is None
    assert store.get_quiz_attempt_count() == 0


def test_record_quiz_attempt_tracks_best_by_percentage(store):
    store.record_quiz_attempt(score=40, total=55)
    store.record_quiz_attempt(score=30, total=55)
    store.record_quiz_attempt(score=45, total=55)

    assert store.get_best_quiz_score() == (45, 55)
    assert store.get_quiz_attempt_count() == 3


def test_reset_progress_clears_quiz_attempts(store):
    store.record_quiz_attempt(score=40, total=55)
    store.reset_progress()
    assert store.get_best_quiz_score() is None


# -- XP / leveling ------------------------------------------------------------
def test_new_profile_starts_at_player_level_one_with_no_xp(store):
    player = store.get_player_level()
    assert player.level == 1
    assert player.total_xp == 0
    assert player.xp_into_level == 0
    assert player.xp_needed_for_level == 100


def test_add_xp_accumulates_without_leveling_up(store):
    player = store.add_xp(30)
    assert player.total_xp == 30
    assert player.level == 1
    assert player.xp_into_level == 30

    player = store.add_xp(20)
    assert player.total_xp == 50
    assert player.level == 1
    assert player.xp_into_level == 50


def test_add_xp_crosses_a_level_boundary(store):
    player = store.add_xp(100)
    assert player.level == 2
    assert player.xp_into_level == 0
    assert player.xp_needed_for_level == 200  # level 2 -> 3 costs 200


def test_add_xp_can_cross_multiple_level_boundaries_at_once(store):
    # 100 (lvl1->2) + 200 (lvl2->3) + 50 into level 3 = 350
    player = store.add_xp(350)
    assert player.level == 3
    assert player.xp_into_level == 50
    assert player.xp_needed_for_level == 300


def test_add_xp_zero_is_a_no_op(store):
    before = store.get_player_level()
    after = store.add_xp(0)
    assert after == before


def test_complete_lesson_awards_xp_once_but_not_on_replay(store):
    store.complete_lesson("lesson_01", stars_earned=3)
    assert store.get_player_level().total_xp == 30  # 3 stars * 10 xp

    store.complete_lesson("lesson_01", stars_earned=3)  # replay, same lesson
    assert store.get_player_level().total_xp == 30, "XP should not be farmable by replaying a completed lesson"


def test_record_quiz_attempt_awards_xp_every_time(store):
    store.record_quiz_attempt(score=5, total=5)
    assert store.get_player_level().total_xp == 25  # 5 correct * 5 xp

    store.record_quiz_attempt(score=3, total=5)
    assert store.get_player_level().total_xp == 40  # +15 more


def test_reset_progress_clears_xp(store):
    store.add_xp(250)
    store.reset_progress()
    player = store.get_player_level()
    assert player.total_xp == 0
    assert player.level == 1


# -- weekly summary / activity-since (parent dashboard) -------------------
def test_get_activity_since_excludes_rows_before_the_cutoff(store, monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(days=5)).isoformat())
    store.log_event(None, "lesson_completed", "stars=1")

    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(days=1)).isoformat())
    store.log_event(None, "lesson_completed", "stars=2")

    cutoff = (now - timedelta(days=3)).isoformat()
    rows = store.get_activity_since(cutoff)

    assert len(rows) == 1
    assert rows[0]["detail"] == "stars=2"


def test_weekly_summary_is_all_zero_with_no_activity(store):
    summary = store.get_weekly_summary()
    assert summary.lessons_completed == 0
    assert summary.stars_earned == 0
    assert summary.quiz_attempts == 0
    assert summary.badges_earned == 0
    assert summary.active_days == 0


def test_weekly_summary_excludes_activity_older_than_7_days(store, monkeypatch):
    now = datetime.now(timezone.utc)

    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(days=10)).isoformat())
    store.complete_lesson("lesson_old", 5)  # outside the 7-day window

    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(hours=1)).isoformat())
    store.complete_lesson("lesson_new", 2)
    store.award_badge("first_program")
    store.record_quiz_attempt(9, 10)

    summary = store.get_weekly_summary()
    assert summary.lessons_completed == 1
    assert summary.stars_earned == 2
    assert summary.quiz_attempts == 1
    assert summary.badges_earned == 1
    assert summary.active_days == 1


def test_weekly_summary_sums_stars_across_multiple_completions(store, monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(hours=2)).isoformat())
    store.complete_lesson("lesson_a", 3)
    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(hours=1)).isoformat())
    store.complete_lesson("lesson_b", 4)

    summary = store.get_weekly_summary()
    assert summary.lessons_completed == 2
    assert summary.stars_earned == 7


def test_weekly_summary_active_days_counts_distinct_calendar_dates(store, monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(store_module, "_now", lambda: (now - timedelta(days=2)).isoformat())
    store.complete_lesson("lesson_a", 1)
    store.complete_lesson("lesson_b", 1)  # same day as lesson_a

    monkeypatch.setattr(store_module, "_now", lambda: now.isoformat())
    store.complete_lesson("lesson_c", 1)  # a different day

    summary = store.get_weekly_summary()
    assert summary.active_days == 2


# -- get_recent_failure_count() (adaptive practice / Practice Quest) ----------
def test_recent_failure_count_zero_for_a_never_attempted_lesson(store):
    assert store.get_recent_failure_count("lesson_10") == 0


def test_recent_failure_count_counts_error_and_wrong_output_events(store):
    store.log_event("lesson_10", "attempt_error", "x")
    store.log_event("lesson_10", "attempt_wrong_output", "y")
    assert store.get_recent_failure_count("lesson_10") == 2


def test_recent_failure_count_counts_timeout_and_blocked_too(store):
    store.log_event("lesson_10", "attempt_timeout")
    store.log_event("lesson_10", "attempt_blocked", "import os")
    assert store.get_recent_failure_count("lesson_10") == 2


def test_recent_failure_count_ignores_unrelated_event_types(store):
    store.log_event("lesson_10", "attempt_error", "x")
    store.log_event("lesson_10", "hint_used", "some hint")
    assert store.get_recent_failure_count("lesson_10") == 1


def test_recent_failure_count_resets_after_a_completion(store):
    store.log_event("lesson_10", "attempt_error", "x")
    store.log_event("lesson_10", "attempt_error", "y")
    store.complete_lesson("lesson_10", 3)
    assert store.get_recent_failure_count("lesson_10") == 0


def test_recent_failure_count_only_counts_failures_after_the_last_completion(store):
    store.log_event("lesson_10", "attempt_error", "before")
    store.complete_lesson("lesson_10", 3)
    store.log_event("lesson_10", "attempt_error", "after")
    assert store.get_recent_failure_count("lesson_10") == 1


def test_recent_failure_count_is_isolated_per_lesson(store):
    store.log_event("lesson_10", "attempt_error", "x")
    store.log_event("lesson_11", "attempt_error", "y")
    store.log_event("lesson_11", "attempt_error", "z")
    assert store.get_recent_failure_count("lesson_10") == 1
    assert store.get_recent_failure_count("lesson_11") == 2


# -- export / import (Settings screen's "Export/Import Progress") ---------
def test_export_progress_data_has_the_expected_shape(store):
    store.complete_lesson("lesson_01", stars_earned=3)
    store.award_badge("first_program")
    store.record_quiz_attempt(score=8, total=10)

    data = store.export_progress_data()

    assert data["format_version"] == store_module.PROGRESS_EXPORT_FORMAT_VERSION
    assert "exported_at" in data
    assert data["profile"]["total_stars"] == 3
    assert data["lesson_completions"] == [
        {"lesson_id": "lesson_01", "stars_earned": 3, "completed_at": data["lesson_completions"][0]["completed_at"]}
    ]
    assert data["badges"][0]["badge_id"] == "first_program"
    assert data["quiz_attempts"][0] == {
        "score": 8, "total": 10, "completed_at": data["quiz_attempts"][0]["completed_at"],
    }
    assert data["player_xp"]["total_xp"] == store.get_player_level().total_xp


def test_import_progress_data_round_trips_everything(store, tmp_path):
    store.complete_lesson("lesson_01", stars_earned=3)
    store.complete_lesson("lesson_02", stars_earned=2)
    store.award_badge("first_program")
    store.record_quiz_attempt(score=8, total=10)
    store.log_event("lesson_01", "attempt_wrong_output", "oops")
    exported = store.export_progress_data()

    other = ProgressStore(tmp_path / "other.sqlite3")
    try:
        other.import_progress_data(exported)

        assert sorted(other.get_completed_lesson_ids()) == ["lesson_01", "lesson_02"]
        assert other.get_stars_by_lesson() == store.get_stars_by_lesson()
        assert other.get_badge_ids() == store.get_badge_ids()
        assert other.get_quiz_attempt_count() == store.get_quiz_attempt_count()
        assert other.get_summary() == store.get_summary()
        assert other.get_player_level() == store.get_player_level()
    finally:
        other.close()


def test_import_progress_data_overwrites_existing_progress(store, tmp_path):
    store.complete_lesson("lesson_99", stars_earned=5)
    store.award_badge("game_creator")
    exported_empty = ProgressStore(tmp_path / "empty.sqlite3")
    try:
        empty_export = exported_empty.export_progress_data()
    finally:
        exported_empty.close()

    store.import_progress_data(empty_export)

    assert store.get_completed_lesson_ids() == []
    assert store.get_badge_ids() == []
    assert store.get_summary().total_stars == 0


def test_import_progress_data_rejects_a_file_with_no_format_version(store):
    with pytest.raises(store_module.InvalidProgressFile):
        store.import_progress_data({"lesson_completions": []})


def test_import_progress_data_rejects_a_mismatched_format_version(store):
    with pytest.raises(store_module.InvalidProgressFile):
        store.import_progress_data({"format_version": 999})


def test_import_progress_data_rejects_non_dict_input(store):
    with pytest.raises(store_module.InvalidProgressFile):
        store.import_progress_data(["not", "a", "dict"])
