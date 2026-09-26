"""Exercises app_window_flet.main()'s back-navigation fix -- confirm_pop()
must consult the `history` stack instead of letting the hardware back
button close the app outright.

The real bug: ft.View.can_pop defaults to True, which lets Flutter's
Navigator pop a view immediately without asking Python first -- and since
page.views is deliberately kept at length 1 (see that module's docstring),
a "successful" pop always meant closing the app, never revealing a
previous screen, regardless of the `history` stack. Confirmed via
real-device Android testing. The fix sets can_pop=False + on_confirm_pop
on every view built, so Flutter asks first.
"""
from __future__ import annotations

import asyncio

import pytest

from app.ui.app_window_flet import main


class FakeWindow:
    def __init__(self) -> None:
        self.width = None
        self.height = None
        self.icon = None


class FakePage:
    """Just enough of ft.Page's surface for main()'s route dispatch to run
    -- route/views/on_route_change/go(), mirroring how a real Page fires
    on_route_change whenever .go() (or .route =) changes the route."""

    def __init__(self) -> None:
        self.window = FakeWindow()
        self.title = None
        self.padding = None
        self.fonts = None
        self.route = "/"
        self.views: list = []
        self.on_route_change = None
        self.bgcolor = None
        self.theme_mode = None
        self.theme = None
        self.dark_theme = None

    def update(self) -> None:
        pass

    def go(self, route: str) -> None:
        self.route = route
        self.on_route_change(None)


class FakeConfirmableView:
    """Stands in for whatever real ft.View a back-press event's e.control
    would carry -- only needs the async confirm_pop(should_pop) method the
    fix actually calls."""

    def __init__(self) -> None:
        self.confirm_pop_calls: list[bool] = []

    async def confirm_pop(self, should_pop: bool) -> None:
        self.confirm_pop_calls.append(should_pop)


class FakeConfirmPopEvent:
    def __init__(self, control) -> None:
        self.control = control


@pytest.fixture
def page(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    p = FakePage()
    main(p)
    return p


def _trigger_back(page: FakePage) -> FakeConfirmableView:
    """Fires the current view's registered on_confirm_pop handler, as
    Flutter would on a hardware back-button press, and returns the fake
    control so the test can inspect what confirm_pop(should_pop) it got."""
    handler = page.views[-1].on_confirm_pop
    fake_view = FakeConfirmableView()
    asyncio.run(handler(FakeConfirmPopEvent(fake_view)))
    return fake_view


def test_every_view_gets_can_pop_false(page):
    page.go("/hub")
    assert page.views[-1].can_pop is False
    assert page.views[-1].on_confirm_pop is not None


def test_back_from_dashboard_navigates_to_hub_instead_of_letting_flutter_pop(page):
    page.go("/hub")
    page.go("/dashboard")

    fake_view = _trigger_back(page)

    assert page.route == "/hub"
    # should_pop=False -- we navigated ourselves via page.go(), so Flutter
    # must NOT also pop (which would have nothing left to reveal and close
    # the app, the exact bug this fixes).
    assert fake_view.confirm_pop_calls == [False]


def test_back_from_hub_with_empty_history_lets_the_pop_proceed(page):
    page.go("/hub")

    fake_view = _trigger_back(page)

    # Nothing to navigate back to -- let the pop (and therefore the app
    # close, since there's only ever one view) actually happen.
    assert fake_view.confirm_pop_calls == [True]


def test_back_navigates_through_multiple_screens_in_order(page):
    page.go("/hub")
    page.go("/dashboard")
    page.go("/settings")

    _trigger_back(page)
    assert page.route == "/dashboard"

    _trigger_back(page)
    assert page.route == "/hub"

    fake_view = _trigger_back(page)
    assert fake_view.confirm_pop_calls == [True]


def test_startup_records_todays_play_and_the_hub_shows_the_welcome_moment_once(page):
    from app.ui.components.adventure_kit_flet import find_by_kind

    # main() called record_play_today() for a fresh profile -> first play
    # today -> the Hub greets the child once, then consumes the moment.
    page.go("/hub")
    banners = find_by_kind(page.views[-1], "welcome_banner")
    assert len(banners) == 1
    assert "Welcome" in banners[0].data["message"]

    page.go("/dashboard")
    page.go("/hub")
    assert find_by_kind(page.views[-1], "welcome_banner") == []


def test_resize_across_the_breakpoint_rebuilds_the_view_without_touching_history(page):
    from app.ui.components.adventure_kit_flet import find_by_kind

    page.width = 400
    page.go("/hub")
    compact_view = page.views[-1]
    assert find_by_kind(compact_view, "content_column") == []

    page.width = 1200
    page.on_resized(None)
    wide_view = page.views[-1]
    assert wide_view is not compact_view
    assert wide_view.route == "/hub"
    assert len(find_by_kind(wide_view, "content_column")) == 1

    # A rebuild is not a navigation: back from the Hub still has nowhere to go.
    fake_view = _trigger_back(page)
    assert fake_view.confirm_pop_calls == [True]


def test_resize_within_the_same_layout_class_does_not_rebuild(page):
    page.width = 400
    page.go("/hub")
    before = page.views[-1]
    page.width = 500
    page.on_resized(None)
    assert page.views[-1] is before


def test_resize_never_rebuilds_a_lesson_in_progress(page):
    page.width = 400
    page.go("/hub")
    page.go("/lesson/lesson_01")
    before = page.views[-1]
    page.width = 1200
    page.on_resized(None)
    assert page.views[-1] is before


def test_closet_route_builds_the_closet_view(page):
    page.go("/hub")
    page.go("/closet")
    assert page.views[-1].route == "/closet"


def test_setup_route_is_never_pushed_to_history(page):
    # main() lands on /setup first (setup_complete defaults to False for a
    # fresh settings file) -- going straight to /hub from there must not
    # leave /setup reachable via back.
    page.go("/hub")

    fake_view = _trigger_back(page)

    assert fake_view.confirm_pop_calls == [True]
