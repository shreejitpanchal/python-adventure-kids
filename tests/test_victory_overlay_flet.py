import flet as ft

from app.ui.components.victory_overlay_flet import build_victory_overlay


class FakePage:
    def __init__(self):
        self.update_count = 0

    def update(self):
        self.update_count += 1


def test_overlay_starts_hidden_with_a_collapsed_badge_card():
    page = FakePage()

    class FakeTheme:
        primary = "#4F8FF7"
        star = "#FFC93C"
        success = "#3FC97A"
        warning = "#FFB238"

    handle = build_victory_overlay(page, FakeTheme(), lambda e: None)
    assert handle.overlay.visible is False
    badge_card = handle.overlay.controls[-1].content
    assert badge_card.scale == 0.0


def test_show_makes_the_overlay_visible_and_springs_the_badge_in():
    page = FakePage()

    class FakeTheme:
        primary = "#4F8FF7"
        star = "#FFC93C"
        success = "#3FC97A"
        warning = "#FFB238"

    handle = build_victory_overlay(page, FakeTheme(), lambda e: None)
    handle.show()

    assert handle.overlay.visible is True
    badge_card = handle.overlay.controls[-1].content
    assert badge_card.scale == 1.0
    dim_background = handle.overlay.controls[0]
    assert dim_background.opacity == 0.85
    assert page.update_count == 1


def test_hide_collapses_everything_back_down():
    page = FakePage()

    class FakeTheme:
        primary = "#4F8FF7"
        star = "#FFC93C"
        success = "#3FC97A"
        warning = "#FFB238"

    handle = build_victory_overlay(page, FakeTheme(), lambda e: None)
    handle.show()
    handle.hide()

    assert handle.overlay.visible is False
    badge_card = handle.overlay.controls[-1].content
    assert badge_card.scale == 0.0
    dim_background = handle.overlay.controls[0]
    assert dim_background.opacity == 0.0


def test_reward_and_badge_text_are_mutable_after_construction():
    page = FakePage()

    class FakeTheme:
        primary = "#4F8FF7"
        star = "#FFC93C"
        success = "#3FC97A"
        warning = "#FFB238"

    handle = build_victory_overlay(page, FakeTheme(), lambda e: None)
    handle.reward_text.value = "🎉 Great job!"
    handle.badge_text.value = "🎖️ New badge!"
    assert handle.reward_text.value == "🎉 Great job!"
    assert handle.badge_text.value == "🎖️ New badge!"


def test_continue_button_fires_the_on_continue_callback():
    page = FakePage()
    calls = []

    class FakeTheme:
        primary = "#4F8FF7"
        star = "#FFC93C"
        success = "#3FC97A"
        warning = "#FFB238"

    handle = build_victory_overlay(page, FakeTheme(), lambda e: calls.append(e))
    badge_card = handle.overlay.controls[-1].content
    continue_gesture = badge_card.content.controls[-1]
    assert isinstance(continue_gesture, ft.GestureDetector)
    continue_gesture.on_tap("fake-event")
    assert calls == ["fake-event"]


def test_real_theme_presets_work_with_the_overlay():
    """Sanity check against the app's actual ThemePreset, not just a fake."""
    from app.ui.theme_flet import get_preset

    page = FakePage()
    theme = get_preset("midnight_dark")
    handle = build_victory_overlay(page, theme, lambda e: None)
    handle.show()
    assert handle.overlay.visible is True
