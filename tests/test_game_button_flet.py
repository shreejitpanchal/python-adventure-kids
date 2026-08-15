import flet as ft

from app.ui.components.game_button_flet import build_game_button


class FakePage:
    def __init__(self):
        self.update_count = 0

    def update(self):
        self.update_count += 1


def test_builds_a_gesture_detector_wrapping_a_container():
    page = FakePage()
    gd = build_game_button("Go", lambda e: None, page, bgcolor="#4F8FF7")
    assert isinstance(gd, ft.GestureDetector)
    container = gd.content
    assert isinstance(container, ft.Container)
    assert container.scale == 1.0
    assert container.bgcolor == "#4F8FF7"
    assert container.content.value == "Go"


def test_tap_down_squeezes_and_tap_up_releases():
    page = FakePage()
    gd = build_game_button("Go", lambda e: None, page, bgcolor="#4F8FF7")
    container = gd.content

    gd.on_tap_down(None)
    assert container.scale == 0.92
    assert page.update_count == 1

    gd.on_tap_up(None)
    assert container.scale == 1.0
    assert page.update_count == 2


def test_tap_cancel_also_releases():
    page = FakePage()
    gd = build_game_button("Go", lambda e: None, page, bgcolor="#4F8FF7")
    container = gd.content

    gd.on_tap_down(None)
    assert container.scale == 0.92

    gd.on_tap_cancel(None)
    assert container.scale == 1.0


def test_on_tap_fires_the_click_callback():
    calls = []
    page = FakePage()
    gd = build_game_button("Go", lambda e: calls.append(e), page, bgcolor="#4F8FF7")
    gd.on_tap("fake-event")
    assert calls == ["fake-event"]


def test_width_and_height_are_applied():
    page = FakePage()
    gd = build_game_button("Go", lambda e: None, page, bgcolor="#4F8FF7", width=240, height=64)
    assert gd.content.width == 240
    assert gd.content.height == 64
