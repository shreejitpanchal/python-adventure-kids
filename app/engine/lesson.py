"""The Lesson data model. Lessons are content, not code — see content/lessons/*.yaml."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Lesson:
    id: str
    title: str
    level: int
    objective: str
    explanation: str
    example_code: str
    starter_code: str
    challenge: str
    expected_output: str = ""
    hints: list[str] = field(default_factory=list)
    reward_stars: int = 1
    badge: Optional[str] = None
    next_lesson_id: Optional[str] = None
    input_prompt: Optional[str] = None
    """If set, the lesson screen shows a labeled input box and feeds its value
    to the sandboxed code's stdin. expected_output may contain "{input}" as a
    placeholder for whatever the child typed."""
    expected_output_pattern: Optional[str] = None
    """A regex alternative to expected_output, for lessons involving
    randomness (games) where multiple outcomes are all valid."""
    graphical: bool = False
    """If true, the lesson runs in-process against a live game window instead
    of the sandboxed subprocess -- see app/games/."""
