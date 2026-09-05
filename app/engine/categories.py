"""Display metadata (title, icon, color) for lesson categories, used by the
category browser -- one distinct, solid color per topic, Scratch-style
(Motion=blue, Looks=purple, Events=gold, ...) so a child can recognize a
category by color alone, not just its label.

Purely presentational -- adding a category here isn't required for the
engine to work (LessonEngine.categories() derives the actual set from
content), but a category without an entry here falls back to a generic
label/color in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMeta:
    title: str
    icon: str
    color: str


CATEGORY_META: dict[str, CategoryMeta] = {
    "basics": CategoryMeta("Python Basics", "🐍", "#4C97FF"),
    "numbers": CategoryMeta("Numbers", "🔢", "#FF9F1C"),
    "addition": CategoryMeta("Addition", "➕", "#4CAF50"),
    "subtraction": CategoryMeta("Subtraction", "➖", "#F06292"),
    "multiplication": CategoryMeta("Multiplication", "✖️", "#9C6ADE"),
    "division": CategoryMeta("Division", "➗", "#26C6DA"),
    "variables": CategoryMeta("Variables", "📦", "#FFCA28"),
    "strings": CategoryMeta("Strings", "🔤", "#EC407A"),
    "input": CategoryMeta("Ask a Question", "🙋", "#29B6F6"),
    "conditionals": CategoryMeta("Decisions", "🚦", "#FF7043"),
    "loops": CategoryMeta("Loops", "🔁", "#26A69A"),
    "functions": CategoryMeta("Functions", "⚙️", "#7E57C2"),
    "lists": CategoryMeta("Lists", "🎒", "#8D6E63"),
    "games": CategoryMeta("Mini Games", "🎮", "#EF5350"),
    "snake": CategoryMeta("Snake Project", "🐍", "#66BB6A"),
    "quiz": CategoryMeta("Quiz", "❓", "#5C6BC0"),
    "code_crackers": CategoryMeta("Code Crackers", "🧩", "#D4A017"),
    "creative_arts": CategoryMeta("Creative Arts", "🎨", "#FF6EC7"),
    "rpg_quests": CategoryMeta("RPG Quests", "⚔️", "#8B4513"),
    "arcade_lab": CategoryMeta("Arcade Lab", "🏓", "#00ACC1"),
    "robot_adventure": CategoryMeta("Robot Adventure", "🤖", "#546E7A"),
    "advanced_code_crackers": CategoryMeta("Advanced Code Crackers", "🕵️", "#37474F"),
    "course_intro_setup": CategoryMeta("Intro to Python & Setup", "🧭", "#4F46E5"),
    "course_variables": CategoryMeta("Variables & Data Types", "🧮", "#0EA5E9"),
    "course_control_flow": CategoryMeta("Control Flow", "🔀", "#F97316"),
    "course_functions": CategoryMeta("Functions", "🧰", "#7C3AED"),
    "course_data_structures": CategoryMeta("Data Structures", "🗂️", "#10B981"),
    "course_advanced_concepts": CategoryMeta("Advanced Programming Concepts", "🧠", "#0891B2"),
    "course_stdlib": CategoryMeta("Standard Library Deep Dive", "📚", "#9333EA"),
    "course_concurrency": CategoryMeta("Concurrency & Observability", "🕸️", "#BE185D"),
    "course_capstone": CategoryMeta("Capstone: To-Do App", "🏁", "#DC2626"),
    "ai_foundations": CategoryMeta("AI Foundations", "🤖", "#7C4DFF"),
    "ai_tools": CategoryMeta("Machine Learning & Tools", "🧠", "#00BFA5"),
    "ai_advanced": CategoryMeta("Advanced AI Concepts", "🧬", "#5E35B1"),
}

DEFAULT_META = CategoryMeta("More Adventures", "⭐", "#78909C")


def get_category_meta(category: str) -> CategoryMeta:
    return CATEGORY_META.get(category, DEFAULT_META)


TOPIC_ICONS: dict[str, str] = {
    "Lists": "📃", "Tuples": "🔗", "Dictionaries": "📖", "Sets": "🧺",
    "Variables": "📦", "Numbers": "🔢", "Strings": "🔤", "Booleans": "🔘",
    "Type Conversion": "🔄",
    "Print": "🖨️", "Comments": "💬", "Reading Errors": "🐞",
    "Conditionals": "🚦", "For Loops": "🔁", "While Loops": "🔂",
    "Defining Functions": "🧰", "Parameters": "🧩", "Return Values": "↩️",
    "Algorithms": "📐", "Recursion": "🪆", "Functional Programming": "🧬",
    "Collections": "🗃️", "Itertools": "🔁", "Datetime": "📅", "JSON": "🧾",
    "Concurrency & Async": "⚡", "Thread Scheduling": "🧵", "Sync vs Async": "🔀",
    "Observability": "🔭",
    "What is AI?": "🤖", "Rule-Based Decisions": "🚦", "Types of AI": "🏷️",
    "What is Machine Learning?": "📊", "What is MCP?": "🔌",
    "Neural Networks": "🕸️", "MCP Framework": "🧰",
}
"""Purely presentational icon per sub-topic name, shown next to a topic's
group heading within a multi-topic course chapter screen (see
app/engine/course_status.py's TopicStatus). A topic with no entry here
just renders without an icon -- this is cosmetic only, never required."""


def get_topic_icon(topic: str) -> str:
    return TOPIC_ICONS.get(topic, "")


PROJECT_CATEGORIES = ["games", "snake", "creative_arts", "rpg_quests", "arcade_lab", "robot_adventure"]
"""The "Build a Project" grouping for the Learning Hub -- every category
that isn't a core skill-practice track (see LessonEngine.TODAYS_MISSION_
CATEGORIES), "basics", or one of the two Code Crackers tracks (which get
their own direct Hub cards instead of being lumped in here)."""

COURSE_CATEGORIES = [
    "course_intro_setup", "course_variables", "course_control_flow",
    "course_functions", "course_data_structures", "course_advanced_concepts",
    "course_stdlib", "course_concurrency", "course_capstone",
]
"""The "🎓 Python Learning" course's chapters, in curriculum order -- each
one a lesson category, grouped by Lesson.topic into 3-item sub-groups
(concept lesson, sample-program lesson, quiz) -- see
app/engine/course_status.py's TopicStatus/is_topic_item_unlocked(). A
chapter can hold just one implicit topic (topic="" on every lesson, e.g.
course_intro_setup) or several independent named topics (e.g.
course_data_structures: Lists/Tuples/Dictionaries/Sets, course_variables:
Variables/Numbers/Strings/Booleans/Type Conversion) -- topics within a
chapter are never locked relative to each other, only the 3 items within
one topic gate in order. Never added to LessonEngine.TODAYS_MISSION_
CATEGORIES -- this course is reached only through its own Hub card, not
folded into "Today's Mission"."""

AI_COURSE_CATEGORIES = ["ai_foundations", "ai_tools", "ai_advanced"]
"""The "🤖 AI & Machine Learning" course's chapters, in curriculum order --
a second, standalone course parallel to COURSE_CATEGORIES above, sharing the
same category/topic/quiz-item machinery via app.engine.courses.CourseSpec
rather than a duplicated engine. Deliberately ordered low-to-high level:
ai_foundations covers beginner concepts (What is AI?, Rule-Based Decisions,
Types of AI), ai_tools covers practical/intermediate ones (What is Machine
Learning?, What is MCP?), and ai_advanced covers deeper technical ones
(Neural Networks, MCP Framework). Every concept lesson here teaches AI/ML/MCP
ideas through plain-Python simulation (dicts, if/else) -- the sandbox has no
real ML libraries and never should (see app/sandbox/safety.py), and course
lessons can't use input() either (see the add-course-topic skill). Never
added to LessonEngine.TODAYS_MISSION_CATEGORIES or COURSE_CATEGORIES --
reached only through its own Hub card."""
