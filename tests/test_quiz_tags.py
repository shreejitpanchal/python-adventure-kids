from app.engine.quiz_engine import QuizEngine

# The fixed concept_tags vocabulary -- content/quiz/quiz_questions.yaml must
# only ever use tags from this set. Keep this list in sync with the
# vocabulary documented for content authors.
VOCABULARY = {
    "print", "strings", "numbers", "comments", "expressions", "variables",
    "naming", "input", "type-conversion", "f-strings", "comparison",
    "booleans", "conditionals", "loops", "for-loops", "while-loops",
    "functions", "parameters", "return-values", "lists", "indexing",
    "slicing", "dictionaries", "iteration", "debugging", "errors",
    "algorithms", "random", "classes",
}


def test_every_question_has_a_concept_tags_list():
    engine = QuizEngine()
    session = engine.start_session()
    assert len(session) == 300
    for question in session:
        assert isinstance(question.concept_tags, list)


def test_concept_tags_only_use_the_fixed_vocabulary():
    engine = QuizEngine()
    for question in engine.start_session():
        assert set(question.concept_tags) <= VOCABULARY, (
            f"{question.id} has tags outside the fixed vocabulary: "
            f"{set(question.concept_tags) - VOCABULARY}"
        )


def test_most_questions_have_at_least_one_concept_tag():
    engine = QuizEngine()
    tagged = sum(1 for q in engine.start_session() if q.concept_tags)
    assert tagged >= 250, f"only {tagged}/300 questions have a non-empty concept_tags list"
