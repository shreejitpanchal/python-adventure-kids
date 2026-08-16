from app.engine.quiz_engine import QuizEngine


def test_loads_questions_from_content_dir():
    engine = QuizEngine()
    assert len(engine) == 300


def test_every_question_has_four_options_and_a_valid_correct_index():
    engine = QuizEngine()
    for question in engine.start_session():
        assert len(question.options) == 4
        assert 0 <= question.correct < len(question.options)


def test_start_session_returns_every_question_exactly_once():
    engine = QuizEngine()
    session = engine.start_session()
    assert len(session) == len(engine)
    assert {q.id for q in session} == {q.id for q in engine.start_session()}


def test_start_session_preserves_the_correct_answer_text():
    engine = QuizEngine()
    original_by_id = {q.id: q for q in engine.start_session()}
    shuffled = engine.start_session()

    for question in shuffled:
        original = original_by_id[question.id]
        original_correct_text = original.options[original.correct]
        assert question.options[question.correct] == original_correct_text
        assert set(question.options) == set(original.options)


def test_start_session_randomizes_question_order_across_sessions():
    engine = QuizEngine()
    orders = {tuple(q.id for q in engine.start_session()) for _ in range(10)}
    assert len(orders) > 1, "10 sessions produced the same question order every time"


def test_loading_from_custom_path(tmp_path):
    quiz_yaml = tmp_path / "quiz.yaml"
    quiz_yaml.write_text(
        """
questions:
  - id: q1
    question: "1 + 1 = ?"
    options: ["1", "2", "3", "4"]
    correct: 1
    explanation: "1 + 1 is 2."
""",
        encoding="utf-8",
    )
    engine = QuizEngine(quiz_path=quiz_yaml)
    assert len(engine) == 1
    session = engine.start_session()
    assert session[0].options[session[0].correct] == "2"


# -- count-limited sessions --------------------------------------------------
def test_start_session_with_count_returns_exactly_that_many():
    engine = QuizEngine()
    session = engine.start_session(count=5)
    assert len(session) == 5

    session = engine.start_session(count=20)
    assert len(session) == 20


def test_start_session_with_count_picks_distinct_questions():
    engine = QuizEngine()
    session = engine.start_session(count=10)
    assert len({q.id for q in session}) == 10


def test_start_session_with_count_varies_which_questions_are_picked():
    engine = QuizEngine()
    picks = {tuple(sorted(q.id for q in engine.start_session(count=5))) for _ in range(10)}
    assert len(picks) > 1, "10 five-question sessions picked the exact same 5 questions every time"


def test_start_session_count_none_or_over_pool_size_uses_every_question():
    engine = QuizEngine()
    assert len(engine.start_session(count=None)) == len(engine)
    assert len(engine.start_session(count=len(engine) + 50)) == len(engine)


def test_start_session_count_zero_or_negative_falls_back_to_full_set():
    engine = QuizEngine()
    assert len(engine.start_session(count=0)) == len(engine)
    assert len(engine.start_session(count=-3)) == len(engine)


def test_start_session_carries_concept_tags_through_the_reshuffle():
    """concept_tags must survive start_session()'s option-shuffling
    rebuild (app/engine/quiz_engine.py explicitly re-lists every field
    when constructing each session's QuizQuestion) -- adaptive practice
    recommendations after a quiz depend on this."""
    engine = QuizEngine()
    original_by_id = {q.id: q.concept_tags for q in engine.start_session()}
    session = engine.start_session()
    for question in session:
        assert question.concept_tags == original_by_id[question.id]
