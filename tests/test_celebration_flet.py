import random

import flet as ft

from app.ui.components import celebration_flet as celebration
from app.ui.components import motion_flet as motion
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, NoTaskPage

THEME = get_preset("galaxy")


def test_confetti_builds_the_requested_particles_parked_and_invisible():
    confetti = celebration.build_confetti(count=7, rng=random.Random(1))
    assert isinstance(confetti, ft.Stack)
    assert confetti.data == {"kind": "confetti", "fired": False}
    assert len(confetti.controls) == 7
    for particle in confetti.controls:
        assert particle.opacity == 0.0 and particle.offset.x == 0 and particle.offset.y == 0
        x, y = particle.data["target"]
        assert -celebration._SPREAD_X <= x <= celebration._SPREAD_X
        assert celebration._RISE_MIN <= y <= celebration._RISE_MAX
        assert particle.content.value in celebration.CONFETTI_EMOJI


def test_confetti_targets_are_deterministic_for_a_seeded_rng():
    a = celebration.build_confetti(rng=random.Random(42))
    b = celebration.build_confetti(rng=random.Random(42))
    assert [p.data for p in a.controls] == [p.data for p in b.controls]


def test_burst_now_applies_targets_and_reset_parks_again():
    confetti = celebration.build_confetti(count=3, rng=random.Random(2))
    celebration.burst_now(confetti)
    assert confetti.data["fired"] is True
    for particle in confetti.controls:
        assert (particle.offset.x, particle.offset.y) == particle.data["target"]
        assert particle.rotate == particle.data["spin"]
        assert particle.opacity == 1.0
    celebration.reset_confetti(confetti)
    assert confetti.data["fired"] is False
    assert all(p.opacity == 0.0 and p.offset.y == 0 for p in confetti.controls)


def test_play_confetti_schedules_the_flight_or_bursts_immediately():
    confetti = celebration.build_confetti(count=3, rng=random.Random(3))
    page = FakePage()
    assert celebration.play_confetti(page, confetti) is True
    assert confetti.data["fired"] is False, "flight happens on the page loop, not synchronously"
    assert len(page.scheduled(celebration._fly_and_fade)) == 1

    static = celebration.build_confetti(count=3, rng=random.Random(3))
    assert celebration.play_confetti(NoTaskPage(), static) is False
    assert static.data["fired"] is True


def test_star_row_reveals_earned_stars_and_marks_the_missing_ones():
    row = celebration.build_star_row(THEME, 3, 1.0)
    slots = row.content.controls
    assert len(slots) == 3 and row.data == {"kind": "star_row", "max": 3, "earned": None}
    assert all(s.opacity == 0.0 and s.scale == 0.2 for s in slots)

    page = FakePage()
    assert celebration.reveal_stars(page, row, 2, THEME) is True
    assert row.data["earned"] == 2
    assert [s.content.value for s in slots] == ["⭐", "⭐", "☆"]
    assert all(s.opacity == 0.0 for s in slots), "the pop-in runs on the page loop"
    assert len(page.scheduled(celebration._reveal_stars)) == 1

    static = celebration.build_star_row(THEME, 3, 1.0)
    assert celebration.reveal_stars(NoTaskPage(), static, 3, THEME) is False
    assert all(s.opacity == 1.0 and s.scale == 1.0 for s in static.content.controls)

    celebration.reset_star_row(static)
    assert all(s.opacity == 0.0 for s in static.content.controls) and static.data["earned"] is None


class DialogPage(FakePage):
    def __init__(self) -> None:
        super().__init__()
        self.dialogs: list = []
        self.popped = 0

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        self.popped += 1


def test_badge_unlock_shows_a_dialog_naming_the_badge_and_spins_it_in():
    page = DialogPage()
    assert celebration.show_badge_unlock(page, THEME, "first_program", 1.0) is True
    (dialog,) = page.dialogs
    assert dialog.data["badge_id"] == "first_program"
    assert dialog.data["title"] == "First Program"
    assert len(page.run_task_calls) == 1  # the spin-in
    dialog.actions[0].on_click(None)
    assert page.popped == 1


def test_badge_unlock_is_skipped_on_a_page_without_dialogs():
    assert celebration.show_badge_unlock(FakePage(), THEME, "first_program", 1.0) is False


def test_level_up_banner_shows_the_level_and_hides_again():
    banner = celebration.build_level_up_banner(THEME, 1.0)
    assert banner.visible is False and banner.data["level"] is None

    page = FakePage()
    celebration.show_level_up(page, banner, 3)
    assert banner.visible is True and banner.data["level"] == 3
    assert "Level 3" in banner.content.controls[1].value
    assert "now a" not in banner.content.controls[1].value
    assert len(page.scheduled(motion._pop)) == 1

    celebration.show_level_up(page, banner, 3, title="Bug Hunter")
    assert "You're now a Bug Hunter!" in banner.content.controls[1].value
    assert banner.data["title"] == "Bug Hunter"

    celebration.hide_level_up(banner)
    assert banner.visible is False and banner.data["level"] is None
