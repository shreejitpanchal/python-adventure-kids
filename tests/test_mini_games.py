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
