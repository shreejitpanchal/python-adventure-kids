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
    """Legacy/unused: LessonEngine.next_after() no longer reads this --
    "Today's Mission" order is computed live from category/category_level
    (see LessonEngine.main_path_lessons()) instead of a hand-authored
    chain. Kept on the schema only because some existing lesson YAML still
    sets it; not worth rewriting those files just to clear an inert field."""
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
    category: str = "basics"
    """Groups lessons for the category browser (e.g. "addition"). See
    app/engine/categories.py for display titles/icons."""
    category_level: int = 1
    """This lesson's position within its category (1-based). A level is
    unlocked once every lower category_level in the same category is
    completed."""
    main_path: bool = True
    """Legacy/unused: LessonEngine.main_path_lessons() no longer reads this
    -- "Today's Mission" is now computed live from category/category_level
    (see that method and LessonEngine.TODAYS_MISSION_CATEGORIES) instead of
    this flag. Kept on the schema only because ~240 bonus-level YAML files
    already set main_path: false; removing the field would mean rewriting
    every one of them just to drop an inert key."""
    ast_contains: Optional[list[str]] = None
    """Structural constructs the submitted code must contain (see
    app.engine.validator.validate_ast_contains) -- checked in addition to
    expected_output/expected_output_pattern when set, not instead of it.
    For lessons where matching output alone isn't enough to confirm the
    child used the taught construct (e.g. "Code Crackers" debugging
    exercises)."""
    requires_goal_reached: bool = False
    """If true (graphical lessons only), the lesson also requires
    game.robot_at_goal() to be True after running -- not just "ran without
    raising" -- see app/ui/lesson_screen_flet.py's _on_run_graphical()."""
    concept_tags: list[str] = field(default_factory=list)
    """Which concepts this lesson teaches, from a fixed vocabulary (print,
    strings, numbers, comments, expressions, variables, naming, input,
    type-conversion, f-strings, comparison, booleans, conditionals, loops,
    for-loops, while-loops, functions, parameters, return-values, lists,
    indexing, slicing, dictionaries, iteration, debugging, errors,
    algorithms, random, classes) -- used by LessonEngine.recommend_practice()
    to suggest relevant practice after repeated failures or a quiz. Empty
    is the common case; only lessons wired into the adaptive-practice pool
    need this set."""
