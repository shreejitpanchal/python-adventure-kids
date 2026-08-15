from app.engine.quiz_engine import QuizEngine


def test_loads_questions_from_content_dir():
    engine = QuizEngine()
    assert len(engine) >= 50
    assert len(engine) <= 60


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
