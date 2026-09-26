from app.engine.quests import (
    QUEST_POOL, QUESTS_PER_DAY, all_quests_done, daily_quests, quest_progress,
)


def _by_id(quest_id):
    return next(q for q in QUEST_POOL if q.id == quest_id)


def test_daily_quests_are_three_distinct_pool_entries_in_pool_order_and_stable_for_a_date():
    picked = daily_quests("2026-09-26")
    assert len(picked) == QUESTS_PER_DAY
    assert len({q.id for q in picked}) == QUESTS_PER_DAY
    assert [QUEST_POOL.index(q) for q in picked] == sorted(QUEST_POOL.index(q) for q in picked)
    assert daily_quests("2026-09-26") == picked, "same board all day"


def test_quest_progress_counts_each_kind_of_event():
    events = [
        ("lesson_01", "hint_used", "try this"),
        ("lesson_01", "lesson_completed", "stars=2"),
        ("lesson_02", "lesson_completed", "stars=3"),
        (None, "chest_opened", "xp=25"),
        (None, "quiz_completed", "score=5/10"),
        ("lesson_02", "attempt_wrong_output", "nope"),
    ]
    statuses = {s.quest.id: s for s in quest_progress(QUEST_POOL, events)}
    assert statuses["finish_lesson"].progress == 2 and statuses["finish_lesson"].done
    assert statuses["finish_two"].progress == 2 and statuses["finish_two"].done
    assert statuses["earn_stars"].progress == 5 and statuses["earn_stars"].done
    assert statuses["open_chest"].done
    assert statuses["play_quiz"].done
    # lesson_01 used a hint, lesson_02 didn't -> one hint-free pass
    assert statuses["no_hints"].progress == 1 and statuses["no_hints"].done


def test_quest_progress_with_no_events_is_all_zero_and_not_done():
    statuses = quest_progress(QUEST_POOL, [])
    assert all(s.progress == 0 and not s.done for s in statuses)
    assert all_quests_done(statuses) is False


def test_shown_progress_is_capped_at_the_target():
    events = [("l1", "lesson_completed", "stars=3")] * 5
    (status,) = quest_progress([_by_id("finish_two")], events)
    assert status.progress == 5 and status.shown_progress == 2


def test_malformed_star_detail_counts_as_zero():
    (status,) = quest_progress([_by_id("earn_stars")], [("l1", "lesson_completed", "stars=lots")])
    assert status.progress == 0


def test_all_quests_done_requires_every_quest_and_a_non_empty_board():
    events = [("l1", "lesson_completed", "stars=3")]
    statuses = quest_progress([_by_id("finish_lesson"), _by_id("open_chest")], events)
    assert all_quests_done(statuses) is False
    assert all_quests_done([]) is False
    assert all_quests_done(quest_progress([_by_id("finish_lesson")], events)) is True
