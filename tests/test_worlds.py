import pytest

from app.engine.badges import BADGE_META
from app.engine.categories import CATEGORY_META
from app.engine.lesson_engine import LessonEngine
from app.engine.worlds import (
    UNCHARTED, WORLDS, newly_completed_world, world_badge_id, world_for_category, world_status, worlds_in_order,
)


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_every_lesson_category_belongs_to_a_named_world(engine):
    for category in engine.categories():
        assert world_for_category(category) is not UNCHARTED, f"{category} is unmapped"


def test_every_registered_category_except_the_standalone_quiz_belongs_to_a_world():
    for category in CATEGORY_META:
        if category == "quiz":
            continue
        assert world_for_category(category) is not UNCHARTED, f"{category} is unmapped"


def test_no_category_is_claimed_by_two_worlds():
    seen: dict[str, str] = {}
    for world in WORLDS:
        for category in world.categories:
            assert category not in seen, f"{category} in both {seen[category]} and {world.id}"
            seen[category] = world.id


def test_every_world_has_a_badge_in_the_registry():
    for world in WORLDS:
        assert world_badge_id(world) in BADGE_META, f"missing badge for {world.id}"


def test_unknown_category_falls_back_to_uncharted():
    assert world_for_category("not_a_category") is UNCHARTED


def test_worlds_in_order_groups_by_first_appearance_and_keeps_category_order():
    grouped = worlds_in_order(["basics", "numbers", "variables", "addition", "mystery"])
    assert [(world.id, categories) for world, categories in grouped] == [
        ("word_valley", ["basics", "variables"]),
        ("number_kingdom", ["numbers", "addition"]),
        ("uncharted", ["mystery"]),
    ]


def test_worlds_in_order_follows_the_curriculum_so_the_map_starts_where_the_child_does(engine):
    first_world, first_categories = worlds_in_order(engine.categories())[0]
    assert first_categories[0] == engine.categories()[0]


def test_world_status_counts_lessons_and_flags_completion(engine):
    world = world_for_category("code_crackers")  # Bug Swamp: two categories
    lessons = [
        lesson for category in world.categories for lesson in engine.lessons_in_category(category)
    ]
    empty = world_status(engine, world, set())
    assert (empty.done, empty.total, empty.complete) == (0, len(lessons), False)

    partial = world_status(engine, world, {lessons[0].id})
    assert partial.done == 1 and partial.complete is False

    full = world_status(engine, world, {lesson.id for lesson in lessons})
    assert full.complete is True


def test_world_status_can_be_scoped_to_a_subset_of_categories(engine):
    world = world_for_category("code_crackers")
    only_crackers = engine.lessons_in_category("code_crackers")
    scoped = world_status(engine, world, {lesson.id for lesson in only_crackers}, categories=["code_crackers"])
    assert scoped.complete is True


def test_garden_grows_with_completion():
    from app.engine.worlds import GARDEN_STAGES, garden_stage

    assert garden_stage(0, 0) == GARDEN_STAGES[0]
    assert garden_stage(0, 10) == GARDEN_STAGES[0]
    assert garden_stage(1, 10) == GARDEN_STAGES[1]
    assert garden_stage(4, 10) == GARDEN_STAGES[2]
    assert garden_stage(7, 10) == GARDEN_STAGES[3]
    assert garden_stage(10, 10) == GARDEN_STAGES[4]
    stages = [garden_stage(d, 10) for d in range(11)]
    assert [GARDEN_STAGES.index(s) for s in stages] == sorted(GARDEN_STAGES.index(s) for s in stages)


def test_newly_completed_world_fires_only_on_the_transition(engine):
    world = world_for_category("code_crackers")
    all_ids = {
        lesson.id for category in world.categories for lesson in engine.lessons_in_category(category)
    }
    last = next(iter(all_ids))
    before = all_ids - {last}

    assert newly_completed_world(engine, "code_crackers", before, all_ids) is world
    assert newly_completed_world(engine, "code_crackers", all_ids, all_ids) is None, "already complete"
    assert newly_completed_world(engine, "code_crackers", set(), before) is None, "not complete yet"
    assert newly_completed_world(engine, "not_a_category", set(), all_ids) is None
