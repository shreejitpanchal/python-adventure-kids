from app.progress.store import PlayToday
from app.ui.components import motion_flet as motion
from app.ui.components.streak_flame_flet import (
    build_streak_chip, build_welcome_banner, streak_tier, welcome_message,
)
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, NoTaskPage

THEME = get_preset("sunny_light")


def test_streak_tiers_grow_with_days():
    assert streak_tier(0).name == "spark" and streak_tier(0).hot is False
    assert streak_tier(1).name == "ember" and "1 day streak" in streak_tier(1).label
    assert streak_tier(2).hot is False
    assert streak_tier(3).name == "flame" and streak_tier(3).hot is True
    assert streak_tier(7).name == "blaze" and "on fire" in streak_tier(7).label
    assert streak_tier(30).name == "inferno" and "legendary" in streak_tier(30).label
    sizes = [streak_tier(d).size_multiplier for d in (0, 1, 3, 7, 30)]
    assert sizes == sorted(sizes), "the flame never shrinks as the streak grows"


def test_welcome_message_variants():
    assert welcome_message("Sam", None) is None
    assert welcome_message("Sam", PlayToday(False, 5, False, False)) is None
    assert "Day 4 streak, Sam" in welcome_message("Sam", PlayToday(True, 4, True, False))
    assert "Fresh start, Sam" in welcome_message("Sam", PlayToday(True, 1, False, True))
    assert "Welcome, Sam" in welcome_message("Sam", PlayToday(True, 1, False, False))


def test_streak_chip_is_calm_for_a_new_streak_and_hot_after_three_days():
    calm_page = FakePage()
    calm = build_streak_chip(THEME, 1, 1.0, page=calm_page)
    assert calm.data["tier"] == "ember"
    assert calm.gradient is None and calm.bgcolor == THEME.card
    assert calm_page.run_task_calls == [], "no pulse for a calm chip"

    hot_page = FakePage()
    hot = build_streak_chip(THEME, 5, 1.0, page=hot_page)
    assert hot.data["tier"] == "flame" and hot.data["days"] == 5
    assert hot.gradient is not None
    assert len(hot_page.scheduled(motion._pulse)) == 1


def test_streak_chip_without_a_page_never_schedules():
    chip = build_streak_chip(THEME, 10, 1.0, page=None)
    assert chip.data["tier"] == "blaze"


def test_welcome_banner_pops_in_or_settles_immediately():
    page = FakePage()
    banner = build_welcome_banner(THEME, "hello", 1.0, page=page)
    assert banner.data == {"kind": "welcome_banner", "message": "hello"}
    assert banner.content.value == "hello"
    assert banner.scale == 0.6 and len(page.scheduled(motion._pop)) == 1

    settled = build_welcome_banner(THEME, "hello", 1.0, page=NoTaskPage())
    assert settled.scale == 1.0
