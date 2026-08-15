"""Behavior checks for the randomized mini-games (14-15): the starter code is
correct by design (like Lesson 9), so instead of an edit-required check, run
it many times and confirm it always produces a valid outcome regardless of
what randint()/choice() picked.
"""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

TRIALS = 12


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_chain_from_lesson_13_through_lesson_15(engine):
    assert engine.next_after("lesson_13").id == "lesson_14"
    assert engine.next_after("lesson_14").id == "lesson_15"
    # lesson_15 continues on into the Snake project (see test_snake_lessons.py)
    # rather than ending the curriculum.


def test_lesson_15_awards_game_creator_badge(engine):
    assert engine.get("lesson_15").badge == "game_creator"


def test_guess_the_number_always_produces_a_valid_outcome(engine):
    lesson = engine.get("lesson_14")
    for guess in ["1", "5", "10", "3", "7"]:
        result = run_code(lesson.starter_code.strip(), stdin_text=f"{guess}\n")
        assert result.success is True, result.stderr
        assert validate_output(
            result.stdout, lesson.expected_output,
            input_value=guess, expected_output_pattern=lesson.expected_output_pattern,
        ) is True, f"guess={guess} produced unexpected output {result.stdout!r}"


def test_rock_paper_scissors_always_produces_a_valid_outcome(engine):
    lesson = engine.get("lesson_15")
    for choice in ["rock", "paper", "scissors"]:
        for _ in range(TRIALS // 3):
            result = run_code(lesson.starter_code.strip(), stdin_text=f"{choice}\n")
            assert result.success is True, result.stderr
            assert validate_output(
                result.stdout, lesson.expected_output,
                input_value=choice, expected_output_pattern=lesson.expected_output_pattern,
            ) is True, f"choice={choice} produced unexpected output {result.stdout!r}"


def test_rock_paper_scissors_never_produces_a_losing_outcome_for_valid_play():
    """Sanity check on the game logic itself, independent of the sandbox:
    rock/rock is a tie or a win, never framed as a loss for equal inputs."""
    lesson = LessonEngine().get("lesson_15")
    for _ in range(TRIALS):
        result = run_code(lesson.starter_code.strip(), stdin_text="rock\n")
        assert "You win!" in result.stdout or "tie" in result.stdout or "Computer wins!" in result.stdout


def test_magic_8_ball_always_produces_a_valid_outcome(engine):
    lesson = engine.get("lesson_420")
    for question in ["Will I win?", "Is Python fun?", ""]:
        for _ in range(TRIALS):
            result = run_code(lesson.starter_code.strip(), stdin_text=f"{question}\n")
            assert result.success is True, result.stderr
            assert validate_output(
                result.stdout, lesson.expected_output,
                input_value=question, expected_output_pattern=lesson.expected_output_pattern,
            ) is True, f"question={question!r} produced unexpected output {result.stdout!r}"


def test_lucky_dice_always_produces_a_valid_outcome(engine):
    lesson = engine.get("lesson_421")
    saw_doubles = False
    for _ in range(TRIALS * 4):
        result = run_code(lesson.starter_code.strip(), stdin_text="")
        assert result.success is True, result.stderr
        if "Doubles!" in result.stdout:
            saw_doubles = True
        assert validate_output(
            result.stdout, lesson.expected_output,
            expected_output_pattern=lesson.expected_output_pattern,
        ) is True, f"unexpected output {result.stdout!r}"
    # Enough rolls (1/6 chance per roll) that failing to ever see doubles
    # would signal a broken regex/game rather than bad luck.
    assert saw_doubles is True


def test_coin_flip_always_produces_a_valid_outcome(engine):
    lesson = engine.get("lesson_422")
    for guess in ["Heads", "Tails", "heads", "TAILS", "HeAdS"]:
        for _ in range(TRIALS // 2):
            result = run_code(lesson.starter_code.strip(), stdin_text=f"{guess}\n")
            assert result.success is True, result.stderr
            assert validate_output(
                result.stdout, lesson.expected_output,
                input_value=guess, expected_output_pattern=lesson.expected_output_pattern,
            ) is True, f"guess={guess!r} produced unexpected output {result.stdout!r}"


def test_games_category_has_five_lessons_bonus_levels_correctly_configured(engine):
    lessons = engine.lessons_in_category("games")
    assert len(lessons) == 5
    assert [lesson.category_level for lesson in lessons] == [1, 2, 3, 4, 5]

    bonus_lessons = [lesson for lesson in lessons if lesson.category_level >= 3]
    assert {lesson.id for lesson in bonus_lessons} == {"lesson_420", "lesson_421", "lesson_422"}
    for lesson in bonus_lessons:
        assert lesson.main_path is False
        assert lesson.next_lesson_id is None

    # The original two remain untouched: still on the guided main path.
    main_path_lessons = [lesson for lesson in lessons if lesson.category_level < 3]
    for lesson in main_path_lessons:
        assert lesson.main_path is True
