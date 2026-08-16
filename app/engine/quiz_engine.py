"""Loads quiz questions from YAML, kept separate from application code.

Adding a question means editing content/quiz/quiz_questions.yaml -- no code changes here.
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml

from app.engine.quiz import QuizQuestion

DEFAULT_QUIZ_PATH = Path(__file__).resolve().parent.parent.parent / "content" / "quiz" / "quiz_questions.yaml"


class QuizEngine:
    def __init__(self, quiz_path: Path = DEFAULT_QUIZ_PATH):
        data = yaml.safe_load(quiz_path.read_text(encoding="utf-8"))
        self._questions = [QuizQuestion(**q) for q in data["questions"]]

    def __len__(self) -> int:
        return len(self._questions)

    def start_session(self, count: int | None = None) -> list[QuizQuestion]:
        """A freshly randomized set of questions for one quiz playthrough.

        `count` picks how many questions to include, as a random subset
        with no repeats -- pass None, or a value >= the full bank size, to
        use every question. Either way, both which questions are picked
        and each picked question's own option order are re-randomized
        here, so no two playthroughs look the same and the correct answer
        isn't always in the same position.
        """
        if count is not None and 0 < count < len(self._questions):
            pool = random.sample(self._questions, count)
        else:
            pool = list(self._questions)
            random.shuffle(pool)

        session: list[QuizQuestion] = []
        for question in pool:
            paired = list(enumerate(question.options))
            random.shuffle(paired)
            new_options = [text for _, text in paired]
            new_correct = next(i for i, (original_index, _) in enumerate(paired) if original_index == question.correct)
            session.append(QuizQuestion(
                id=question.id,
                question=question.question,
                options=new_options,
                correct=new_correct,
                explanation=question.explanation,
                concept_tags=question.concept_tags,
            ))
        return session
