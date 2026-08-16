"""Coverage checks for the concept_tags field used by
LessonEngine.recommend_practice() (the "Practice Quest" recommendation
feature).

Verifies that concept_tags added to existing lesson YAML files (a) parse
into a list, (b) stick to the fixed tag vocabulary, (c) actually cover a
meaningful chunk of the content set, and (d) produce real cross-lesson
overlap so recommend_practice() has something to recommend.
"""
from app.engine.lesson_engine import LessonEngine

VOCABULARY = {
    "print", "strings", "numbers", "comments", "expressions", "variables",
    "naming", "input", "type-conversion", "f-strings", "comparison",
    "booleans", "conditionals", "loops", "for-loops", "while-loops",
    "functions", "parameters", "return-values", "lists", "indexing",
    "slicing", "dictionaries", "iteration", "debugging", "errors",
    "algorithms", "random", "classes",
}


def test_all_concept_tags_are_lists_within_vocabulary():
    engine = LessonEngine()
    for lesson in engine.all_in_order():
        assert isinstance(lesson.concept_tags, list), (
            f"{lesson.id}.concept_tags should be a list, got {type(lesson.concept_tags)!r}"
        )
        assert set(lesson.concept_tags) <= VOCABULARY, (
            f"{lesson.id} has tag(s) outside the fixed vocabulary: "
            f"{set(lesson.concept_tags) - VOCABULARY}"
        )


def test_at_least_60_lessons_are_tagged():
    engine = LessonEngine()
    tagged = [lesson for lesson in engine.all_in_order() if lesson.concept_tags]
    assert len(tagged) >= 60, (
        f"Expected at least 60 lessons with non-empty concept_tags, found {len(tagged)}"
    )


def test_key_main_path_lessons_have_expected_tags():
    engine = LessonEngine()
    assert "conditionals" in engine.get("lesson_10").concept_tags
    assert "loops" in engine.get("lesson_11").concept_tags
    assert "functions" in engine.get("lesson_12").concept_tags
    assert "lists" in engine.get("lesson_13").concept_tags


def test_recommend_practice_returns_real_recommendations():
    engine = LessonEngine()
    recommendations = engine.recommend_practice("lesson_10", completed_ids=[])
    assert recommendations, "Expected recommend_practice to find lessons sharing a concept tag with lesson_10"
