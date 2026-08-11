from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code


def test_lesson_09_content_is_input_shaped():
    engine = LessonEngine()
    lesson = engine.get("lesson_09")
    assert lesson.input_prompt == "What is your name?"
    assert "{input}" in lesson.expected_output


def test_lesson_09_starter_code_passes_for_any_typed_name():
    engine = LessonEngine()
    lesson = engine.get("lesson_09")

    for typed_name in ("Sam", "Priya", "X"):
        result = run_code(lesson.starter_code.strip(), stdin_text=f"{typed_name}\n")
        assert result.success is True
        assert validate_output(result.stdout, lesson.expected_output, input_value=typed_name) is True


def test_lesson_09_fails_validation_against_a_different_typed_name():
    engine = LessonEngine()
    lesson = engine.get("lesson_09")

    result = run_code(lesson.starter_code.strip(), stdin_text="Sam\n")
    assert validate_output(result.stdout, lesson.expected_output, input_value="NotSam") is False
