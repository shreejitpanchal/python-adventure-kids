from app.engine.titles import LEVEL_TITLES, level_title, next_title_after


def test_tiers_are_ascending_and_start_at_level_one():
    assert LEVEL_TITLES[0].min_level == 1
    mins = [tier.min_level for tier in LEVEL_TITLES]
    assert mins == sorted(mins) and len(set(mins)) == len(mins)


def test_level_title_picks_the_highest_tier_reached():
    assert level_title(1).title == "Curious Coder" and level_title(1).codey_accessory == ""
    assert level_title(2).title == "Curious Coder"
    assert level_title(3).title == "Bug Hunter" and level_title(3).codey_accessory == "🧢"
    assert level_title(4).title == "Bug Hunter"
    assert level_title(16).title == "Python Master" and level_title(16).codey_accessory == "👑"
    assert level_title(99).title == "Python Master"


def test_next_title_after():
    assert next_title_after(1).title == "Bug Hunter"
    assert next_title_after(3).title == "Loop Wizard"
    assert next_title_after(16) is None
