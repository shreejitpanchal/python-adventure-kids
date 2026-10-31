"""pet_flet: the buddy card draws the XP-derived stage and grows feature by
feature."""
from __future__ import annotations

import flet.canvas as cv
import pytest

from app.engine.pet import PET_STAGES, pet_stage
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.components.pet_flet import build_pet_canvas, build_pet_card, pet_shapes
from tests.flet_testing import FakePage, NoTaskPage, one, texts


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def test_each_stage_adds_shapes_on_top_of_the_last():
    counts = [len(pet_shapes(stage, "#3FC97A")) for stage in PET_STAGES[1:]]
    assert counts == sorted(counts) and len(set(counts)) == len(counts)
    egg = pet_shapes(PET_STAGES[0], "#FFB238")
    assert egg and all(isinstance(shape, (cv.Oval, cv.Path, cv.Circle)) for shape in egg)


def test_pet_canvas_is_tagged_with_its_stage():
    canvas = build_pet_canvas(pet_stage(200), "#3FC97A")
    assert canvas.data == {"kind": "pet_canvas", "stage": "sprout"}
    assert isinstance(canvas.content, cv.Canvas)


def test_pet_card_shows_the_stage_bobs_and_fills_its_bar(state):
    state.progress.add_xp(70)
    page = FakePage()
    card = build_pet_card(page, state, scale=1.0, on_click=lambda e: None)
    assert card.data == {"kind": "pet_card", "stage": "hatchling", "total_xp": 70}
    assert "Hatchling" in " ".join(texts(card))
    assert one(card, "pet_canvas").data["stage"] == "hatchling"
    assert one(card, "power_bar").data["ratio"] == 0.2  # 20 of the 100 XP to Sprout
    assert len(page.scheduled(motion._bob)) == 1
    assert card.on_tap_down is not None, "pressable when tappable"

    still = build_pet_card(NoTaskPage(), state, scale=1.0)
    assert still.on_click is None and still.on_tap_down is None
