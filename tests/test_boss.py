"""app/engine/boss.py: when a World boss unlocks, what it asks, what wins."""
from __future__ import annotations

import pytest

from app.engine.badges import BADGE_META
from app.engine.boss import (
    BOSS_PASS_PERCENT, boss_badge_id, boss_beaten, boss_result_line, boss_tags, boss_title, boss_unlocked, boss_won,
    world_by_id,
)
from app.engine.lesson_engine import LessonEngine
from app.engine.worlds import WORLDS


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_every_world_has_a_registered_boss_badge():
    for world in WORLDS:
        assert boss_badge_id(world) in BADGE_META
        assert BADGE_META[boss_badge_id(world)].icon == "⚔️"


def test_world_by_id():
    assert world_by_id("logic_peaks").title == "Logic Peaks"
    assert world_by_id("nowhere") is None


def test_boss_tags_are_the_union_of_the_worlds_lesson_tags(engine):
    world = world_by_id("number_kingdom")
    tags = boss_tags(engine, world)
    expected = set()
    for category in world.categories:
        for lesson in engine.lessons_in_category(category):
            expected.update(lesson.concept_tags or [])
    assert tags == expected and tags


def test_boss_unlocks_only_when_the_whole_world_is_complete(engine):
    world = world_by_id("number_kingdom")
    everything = [lesson.id for category in world.categories for lesson in engine.lessons_in_category(category)]
    assert boss_unlocked(engine, world, []) is False
    assert boss_unlocked(engine, world, everything[:-1]) is False
    assert boss_unlocked(engine, world, everything) is True


def test_boss_won_and_beaten():
    assert boss_won(6, 8) is True  # 75%
    assert boss_won(5, 8) is False  # 62.5% -> 62
    assert boss_won(7, 10) is True and BOSS_PASS_PERCENT == 70
    assert boss_won(0, 0) is False
    world = world_by_id("bug_swamp")
    assert boss_beaten(world, ["boss_bug_swamp"]) is True
    assert boss_beaten(world, ["world_bug_swamp"]) is False


def test_boss_lines():
    world = world_by_id("word_valley")
    assert boss_title(world) == "⚔️ Boss: Word Valley"
    assert "defeated" in boss_result_line(world, True, 8, 8)
    assert "shrugged" in boss_result_line(world, False, 2, 8)
