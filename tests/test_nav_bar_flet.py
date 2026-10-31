"""nav_bar_flet: the bottom tab bar lights the active tab, navigates on the
others, and scene_view mounts it outside the scrolling controls."""
from __future__ import annotations

import flet as ft

from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import scene_view
from app.ui.components.nav_bar_flet import TABS, build_nav_bar, tab_for_route
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, all_of

THEME = get_preset("sunny_light")


def test_tab_for_route_covers_the_tab_world_and_leaves_lessons_out():
    assert tab_for_route("/hub") == "home"
    assert tab_for_route("/categories") == "map"
    assert tab_for_route("/categories/numbers") == "map"
    assert tab_for_route("/boss/logic_peaks") == "map"
    assert tab_for_route("/dashboard") == "mission"
    assert tab_for_route("/cards") == "trophies"
    assert tab_for_route("/closet") == "codey"
    assert tab_for_route("/lesson/lesson_01") is None
    assert tab_for_route("/settings") is None


def test_bar_lights_the_active_tab_and_the_rest_navigate():
    page = FakePage()
    bar = build_nav_bar(page, THEME, "map")
    assert isinstance(bar, ft.BottomAppBar)
    assert bar.data == {"kind": "nav_bar", "active": "map"}
    tabs = all_of(bar, "nav_tab")
    assert [tab.data["tab"] for tab in tabs] == [tab.key for tab in TABS]
    active = [tab for tab in tabs if tab.data["active"]]
    assert len(active) == 1 and active[0].data["tab"] == "map"
    assert active[0].on_click is None and active[0].gradient is not None

    home = next(tab for tab in tabs if tab.data["tab"] == "home")
    home.on_tap_down(None)
    assert home.scale == motion.PRESS_SCALE
    home.on_click(None)
    assert page.routes_visited == ["/hub"]


def test_scene_view_mounts_the_bar_as_the_bottom_app_bar():
    bar = build_nav_bar(FakePage(), THEME, "home")
    view = scene_view("/hub", THEME, [ft.Text("hi")], nav_bar=bar)
    assert view.bottom_appbar is bar
    assert len(view.controls) == 1, "the bar is not part of the scrolling controls"
    assert scene_view("/x", THEME, [ft.Text("hi")]).bottom_appbar is None
