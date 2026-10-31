"""app/engine/pet.py: the buddy's stage is a pure function of total XP."""
from __future__ import annotations

from app.engine.pet import (
    PET_STAGES, newly_reached_stage, next_pet_stage, pet_line, pet_progress, pet_stage,
)


def test_stages_climb_with_xp_and_thresholds_are_ascending():
    thresholds = [stage.min_xp for stage in PET_STAGES]
    assert thresholds == sorted(thresholds) and thresholds[0] == 0
    assert pet_stage(0).id == "egg"
    assert pet_stage(49).id == "egg"
    assert pet_stage(50).id == "hatchling"
    assert pet_stage(10_000).id == "legend"
    sizes = [stage.size for stage in PET_STAGES]
    assert sizes == sorted(sizes), "the buddy only ever grows"


def test_next_stage_and_progress():
    assert next_pet_stage(0).id == "hatchling"
    assert next_pet_stage(10_000) is None
    assert pet_progress(0) == (0, 50)
    assert pet_progress(70) == (20, 100)
    assert pet_progress(10_000) == (0, 0)


def test_pet_line_counts_down_and_celebrates_the_top():
    assert pet_line(0) == "50 XP until it becomes a Hatchling!"
    assert "legend" in pet_line(10_000).lower()


def test_newly_reached_stage_only_on_a_crossing():
    assert newly_reached_stage(0, 30) is None
    assert newly_reached_stage(30, 60).id == "hatchling"
    assert newly_reached_stage(60, 90) is None
    assert newly_reached_stage(0, 400).id == "scamp", "a big jump reports the stage landed on"
