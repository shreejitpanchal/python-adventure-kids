"""Exercises app/engine/learning_path.py against the real
content/learning_path.yaml -- module status transitions, sequential
unlock, current_module, progress_summary, and the migration-free
"catch up" badge helper."""
import pytest

from app.engine.learning_path import LearningPathEngine


@pytest.fixture(scope="module")
def engine():
    return LearningPathEngine()


def test_loads_eight_modules_in_order(engine):
    modules = engine.modules()
    assert len(modules) == 8
    assert [m.order for m in modules] == list(range(1, 9))
    assert modules[0].id == "python-starter"
    assert modules[-1].id == "python-creator"


def test_every_module_lesson_id_exists_in_the_real_lesson_content():
    """Catches a typo'd required_lesson_ids/checkpoint_lesson_id entry in
    learning_path.yaml immediately, rather than surfacing as a confusing
    KeyError deep in a UI screen."""
    from app.engine.lesson_engine import LessonEngine

    learning_path = LearningPathEngine()
    lesson_engine = LessonEngine()
    for module in learning_path.modules():
        for lesson_id in learning_path.module_lesson_ids(module.id):
            assert lesson_engine.has(lesson_id), f"{module.id} references missing lesson {lesson_id}"


def test_module_lesson_ids_is_required_then_checkpoint(engine):
    ids = engine.module_lesson_ids("python-starter")
    assert ids == ["lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"]


# -- module_status() ----------------------------------------------------------
def test_first_module_is_available_with_nothing_completed(engine):
    assert engine.module_status("python-starter", []) == "available"


def test_second_module_is_locked_until_the_first_is_fully_done(engine):
    assert engine.module_status("variables-and-input", []) == "locked"

    partial = {"lesson_01"}
    assert engine.module_status("variables-and-input", partial) == "locked"


def test_module_becomes_in_progress_once_one_lesson_is_done(engine):
    completed = {"lesson_01"}
    assert engine.module_status("python-starter", completed) == "in_progress"


def test_module_becomes_completed_once_every_required_lesson_and_the_checkpoint_are_done(engine):
    completed = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.module_status("python-starter", completed) == "completed"


def test_module_unlocks_once_the_previous_module_is_fully_complete(engine):
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.module_status("variables-and-input", module_1_done) == "available"


def test_is_module_complete_matches_module_status(engine):
    completed = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.is_module_complete("python-starter", completed) is True
    assert engine.is_module_complete("python-starter", {"lesson_01"}) is False


# -- is_lesson_unlocked() ------------------------------------------------------
def test_first_lesson_in_an_available_module_is_unlocked(engine):
    assert engine.is_lesson_unlocked("python-starter", "lesson_01", []) is True


def test_later_lesson_requires_earlier_ones_completed_first(engine):
    assert engine.is_lesson_unlocked("python-starter", "lesson_02", []) is False
    assert engine.is_lesson_unlocked("python-starter", "lesson_02", {"lesson_01"}) is True


def test_checkpoint_requires_all_required_lessons_first(engine):
    almost = {"lesson_01", "lesson_02", "lesson_03"}  # missing lesson_450
    assert engine.is_lesson_unlocked("python-starter", "lesson_451", almost) is False
    full = almost | {"lesson_450"}
    assert engine.is_lesson_unlocked("python-starter", "lesson_451", full) is True


def test_no_lesson_in_a_locked_module_is_unlocked(engine):
    assert engine.is_lesson_unlocked("variables-and-input", "lesson_07", []) is False


def test_unrelated_lesson_id_is_not_unlocked_for_a_module_it_is_not_in(engine):
    assert engine.is_lesson_unlocked("python-starter", "lesson_10", []) is False


# -- current_module() / progress_summary() -------------------------------------
def test_current_module_with_no_progress_is_the_first_module(engine):
    assert engine.current_module([]).id == "python-starter"


def test_current_module_advances_past_completed_modules(engine):
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.current_module(module_1_done).id == "variables-and-input"


def test_current_module_is_the_last_module_when_everything_is_complete(engine):
    all_ids = {lesson_id for module in engine.modules() for lesson_id in engine.module_lesson_ids(module.id)}
    assert engine.current_module(all_ids).id == "python-creator"


def test_progress_summary_counts_completed_modules(engine):
    assert engine.progress_summary([]) == (0, 8)
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.progress_summary(module_1_done) == (1, 8)


def test_all_modules_complete_false_until_every_module_is_done(engine):
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    assert engine.all_modules_complete(module_1_done) is False

    all_ids = {lesson_id for module in engine.modules() for lesson_id in engine.module_lesson_ids(module.id)}
    assert engine.all_modules_complete(all_ids) is True


# -- newly_earned_module_badges() (the migration-free "catch up" story) -------
def test_newly_earned_module_badges_is_empty_with_no_progress(engine):
    assert engine.newly_earned_module_badges([], []) == []


def test_newly_earned_module_badges_catches_up_a_module_finished_before_this_feature_existed(engine):
    """Simulates a returning child who completed Module 1's lessons the
    OLD way (main-path progression), before Python Journey ever showed
    them a course map -- badges/get_badge_ids() has nothing for this
    module yet, so it must be reported as newly earned."""
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    already_awarded: list[str] = []  # no badges yet -- the "cold start" case
    newly_earned = engine.newly_earned_module_badges(module_1_done, already_awarded)
    assert newly_earned == ["module_python_starter"]


def test_newly_earned_module_badges_does_not_repeat_an_already_awarded_badge(engine):
    module_1_done = {"lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"}
    already_awarded = ["module_python_starter"]
    assert engine.newly_earned_module_badges(module_1_done, already_awarded) == []


def test_newly_earned_module_badges_can_report_more_than_one_at_once(engine):
    """A child who completed lessons across several modules' worth of
    content in one old-style session (before Journey existed) should get
    every satisfied module's badge in one catch-up pass, not just one."""
    completed = {
        "lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451",  # module 1
        "lesson_07", "lesson_09", "lesson_314", "lesson_452",  # module 2
    }
    newly_earned = engine.newly_earned_module_badges(completed, [])
    assert set(newly_earned) == {"module_python_starter", "module_variables_and_input"}
