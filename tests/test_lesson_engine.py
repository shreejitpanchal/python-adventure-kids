from app.engine.lesson_engine import TODAYS_MISSION_CATEGORIES, LessonEngine


def test_loads_lesson_01_from_content_dir():
    engine = LessonEngine()
    assert engine.has("lesson_01")
    lesson = engine.get("lesson_01")
    assert lesson.title
    assert lesson.expected_output == "Hello!"
    assert lesson.starter_code.strip() == 'print("Hello!")'


def test_first_lesson_is_lowest_level():
    engine = LessonEngine()
    assert engine.first().id == "lesson_01"


def test_next_after_last_lesson_is_none():
    engine = LessonEngine()
    last = engine.all_in_order()[-1]
    assert engine.next_after(last.id) is None


# -- Today's Mission: main_path_lessons() round-robin -----------------------
def test_main_path_lessons_starts_with_the_basics_intro():
    engine = LessonEngine()
    assert engine.main_path_lessons()[0].id == "lesson_01"


def test_main_path_lessons_does_every_categorys_level_1_before_any_level_2():
    engine = LessonEngine()
    sequence = engine.main_path_lessons()
    level_1_positions = [
        i for i, lesson in enumerate(sequence)
        if lesson.category in TODAYS_MISSION_CATEGORIES and lesson.category_level == 1
    ]
    level_2_positions = [
        i for i, lesson in enumerate(sequence)
        if lesson.category in TODAYS_MISSION_CATEGORIES and lesson.category_level == 2
    ]
    assert len(level_1_positions) == len(TODAYS_MISSION_CATEGORIES)
    assert max(level_1_positions) < min(level_2_positions)


def test_main_path_lessons_excludes_categories_outside_the_rotation():
    engine = LessonEngine()
    sequence_categories = {lesson.category for lesson in engine.main_path_lessons()}
    assert sequence_categories == {"basics", *TODAYS_MISSION_CATEGORIES}


def test_loading_from_custom_dir(tmp_path):
    lesson_yaml = tmp_path / "lesson_a.yaml"
    lesson_yaml.write_text(
        """
id: lesson_a
title: "A"
level: 1
objective: "obj"
explanation: "exp"
example_code: "print(1)"
starter_code: "print(1)"
challenge: "go"
expected_output: "1"
hints: []
reward_stars: 1
badge: null
next_lesson_id: lesson_b
""",
        encoding="utf-8",
    )
    lesson_yaml_b = tmp_path / "lesson_b.yaml"
    lesson_yaml_b.write_text(
        """
id: lesson_b
title: "B"
level: 2
objective: "obj"
explanation: "exp"
example_code: "print(2)"
starter_code: "print(2)"
challenge: "go"
expected_output: "2"
hints: []
reward_stars: 1
badge: null
next_lesson_id: null
""",
        encoding="utf-8",
    )

    engine = LessonEngine(content_dir=tmp_path)
    assert len(engine) == 2
    assert engine.first().id == "lesson_a"
    assert engine.next_after("lesson_a").id == "lesson_b"
    assert engine.next_after("lesson_b") is None


def test_resolve_current_with_no_progress_returns_first_lesson():
    engine = LessonEngine()
    assert engine.resolve_current(completed_ids=[], stored_current_id=None).id == "lesson_01"


def test_resolve_current_trusts_a_valid_incomplete_stored_id():
    engine = LessonEngine()
    lesson = engine.resolve_current(completed_ids=["lesson_01"], stored_current_id="lesson_03")
    assert lesson.id == "lesson_03"


def test_resolve_current_ignores_a_stored_id_that_is_already_completed():
    engine = LessonEngine()
    lesson = engine.resolve_current(completed_ids=["lesson_01"], stored_current_id="lesson_01")
    assert lesson.id == "lesson_02"


def test_resolve_current_ignores_an_unknown_stored_id():
    engine = LessonEngine()
    lesson = engine.resolve_current(completed_ids=[], stored_current_id="does_not_exist")
    assert lesson.id == "lesson_01"


def test_resolve_current_finds_first_gap_even_without_a_stored_pointer():
    engine = LessonEngine()
    lesson = engine.resolve_current(completed_ids=["lesson_01", "lesson_02"], stored_current_id=None)
    assert lesson.id == "lesson_03"


def test_resolve_current_returns_last_main_path_lesson_when_everything_is_complete():
    engine = LessonEngine()
    all_ids = [lesson.id for lesson in engine.all_in_order()]
    lesson = engine.resolve_current(completed_ids=all_ids, stored_current_id=None)
    assert lesson.id == engine.main_path_lessons()[-1].id


# -- category_completion() (parent dashboard mastery card) ------------------
def test_category_completion_covers_every_category_with_no_completions():
    engine = LessonEngine()
    completion = engine.category_completion(completed_ids=[])
    assert set(completion) == set(engine.categories())
    for done, total in completion.values():
        assert done == 0
        assert total > 0


def test_category_completion_counts_only_lessons_in_that_category():
    engine = LessonEngine()
    completion = engine.category_completion(completed_ids=["lesson_01", "lesson_08"])
    assert completion["basics"] == (1, len(engine.lessons_in_category("basics")))
    assert completion["strings"][0] == 1
    assert completion["strings"][1] == len(engine.lessons_in_category("strings"))
    assert completion["numbers"] == (0, len(engine.lessons_in_category("numbers")))


def test_category_completion_is_fully_done_when_every_lesson_in_it_is_completed():
    engine = LessonEngine()
    strings_ids = [lesson.id for lesson in engine.lessons_in_category("strings")]
    completion = engine.category_completion(completed_ids=strings_ids)
    done, total = completion["strings"]
    assert done == total == 20


def test_category_completion_ignores_unrelated_completed_ids():
    engine = LessonEngine()
    completion = engine.category_completion(completed_ids=["not_a_real_lesson_id"])
    for done, _total in completion.values():
        assert done == 0


# -- recommend_practice() / recommend_practice_for_tags() (adaptive practice) -
def _clean_slate_engine() -> LessonEngine:
    """A LessonEngine with every lesson's concept_tags cleared, so a test
    only sees the tags it explicitly sets -- real content's own tags
    (which legitimately change over time as more lessons get tagged)
    would otherwise leak extra, untested-for candidates into these
    recommend_practice() assertions."""
    engine = LessonEngine()
    for lesson in engine.all_in_order():
        lesson.concept_tags = []
    return engine


def test_recommend_practice_returns_lessons_sharing_a_tag():
    engine = _clean_slate_engine()
    engine.get("lesson_10").concept_tags = ["conditionals"]
    engine.get("lesson_09").concept_tags = ["conditionals"]
    engine.get("lesson_11").concept_tags = ["loops"]

    recommendations = engine.recommend_practice("lesson_10", completed_ids=[])
    assert "lesson_09" in {lesson.id for lesson in recommendations}
    assert "lesson_11" not in {lesson.id for lesson in recommendations}


def test_recommend_practice_excludes_the_struggling_lesson_itself():
    engine = _clean_slate_engine()
    engine.get("lesson_10").concept_tags = ["conditionals"]
    engine.get("lesson_09").concept_tags = ["conditionals"]

    recommendations = engine.recommend_practice("lesson_10", completed_ids=[])
    assert "lesson_10" not in {lesson.id for lesson in recommendations}


def test_recommend_practice_is_empty_when_the_lesson_has_no_tags():
    engine = _clean_slate_engine()
    assert engine.recommend_practice("lesson_10", completed_ids=[]) == []


def test_recommend_practice_respects_the_limit():
    engine = _clean_slate_engine()
    engine.get("lesson_10").concept_tags = ["conditionals"]
    for lesson_id in ["lesson_09", "lesson_11", "lesson_12", "lesson_13"]:
        engine.get(lesson_id).concept_tags = ["conditionals"]

    recommendations = engine.recommend_practice("lesson_10", completed_ids=[], limit=2)
    assert len(recommendations) == 2


def test_recommend_practice_prefers_not_yet_completed_lessons():
    engine = _clean_slate_engine()
    engine.get("lesson_10").concept_tags = ["conditionals"]
    engine.get("lesson_09").concept_tags = ["conditionals"]
    engine.get("lesson_11").concept_tags = ["conditionals"]

    recommendations = engine.recommend_practice("lesson_10", completed_ids=["lesson_09"], limit=1)
    assert recommendations[0].id == "lesson_11"


def test_recommend_practice_for_tags_matches_the_union_of_given_tags():
    engine = _clean_slate_engine()
    engine.get("lesson_09").concept_tags = ["input"]
    engine.get("lesson_10").concept_tags = ["conditionals"]
    engine.get("lesson_11").concept_tags = ["loops"]

    recommendations = engine.recommend_practice_for_tags({"input", "loops"}, completed_ids=[])
    ids = {lesson.id for lesson in recommendations}
    assert ids == {"lesson_09", "lesson_11"}


def test_recommend_practice_for_tags_empty_tag_set_returns_nothing():
    engine = LessonEngine()
    assert engine.recommend_practice_for_tags(set(), completed_ids=[]) == []
