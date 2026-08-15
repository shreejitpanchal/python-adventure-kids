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

    def start_session(self) -> list[QuizQuestion]:
        """A freshly shuffled copy of every question for one quiz playthrough.

        Both the question order and each question's own option order are
        re-randomized here, so the correct answer isn't always in the same
        position and no two playthroughs look the same.
        """
        session: list[QuizQuestion] = []
        for question in self._questions:
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
            ))
        random.shuffle(session)
        return session
