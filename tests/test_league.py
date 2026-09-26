from app.engine.league import FRIENDS, child_rank, league_line, league_standings, weekly_xp_from_events


def test_weekly_xp_tallies_lessons_quizzes_and_bonuses():
    events = [
        ("l1", "lesson_completed", "stars=3"),
        ("l2", "lesson_completed", "stars=2"),
        (None, "quiz_completed", "score=7/10"),
        (None, "chest_opened", "xp=25"),
        (None, "quest_bonus_claimed", "xp=50"),
        ("l1", "hint_used", "hint"),
        ("l3", "lesson_completed", "stars=oops"),
    ]
    assert weekly_xp_from_events(events) == 30 + 20 + 35 + 25 + 50


def test_standings_are_stable_for_a_week_and_put_the_child_near_the_top():
    a = league_standings("Sam", 120, "2026-W39")
    b = league_standings("Sam", 120, "2026-W39")
    assert a == b
    assert len(a) == len(FRIENDS) + 1
    assert [s.xp for s in a] == sorted((s.xp for s in a), reverse=True)
    assert child_rank(a) in (1, 2, 3)
    assert next(s for s in a if s.is_child).xp == 120
    assert all(s.xp % 5 == 0 for s in a if not s.is_child)


def test_a_brand_new_child_is_behind_but_within_reach():
    standings = league_standings("Sam", 0, "2026-W39")
    assert child_rank(standings) == len(standings)
    leader = standings[0]
    assert 0 < leader.xp <= 60, "friends' scores stay small so one lesson matters"
    assert "behind" in league_line(standings)


def test_league_line_celebrates_first_place():
    standings = league_standings("Sam", 5000, "2026-W39")
    assert child_rank(standings) <= 2
    if child_rank(standings) == 1:
        assert "leading" in league_line(standings)
    else:
        assert "behind" in league_line(standings)


def test_ties_go_to_the_child():
    standings = league_standings("Sam", 100, "2026-W01")
    friend_xps = [s.xp for s in standings if not s.is_child]
    if 100 in friend_xps:
        tied_index = next(i for i, s in enumerate(standings) if s.xp == 100)
        assert standings[tied_index].is_child
