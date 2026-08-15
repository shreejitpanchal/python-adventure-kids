"""The QuizQuestion data model. Quiz content is data, not code -- see content/quiz/quiz_questions.yaml."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuizQuestion:
    id: str
    question: str
    options: list[str]
    correct: int
    explanation: str = ""
