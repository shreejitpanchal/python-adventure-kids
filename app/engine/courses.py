"""The registry of standalone Learning Hub courses (currently "🎓 Python
Learning" and "🤖 AI & Machine Learning"). A CourseSpec is the thin
parameter object both UIs' course_map/course_chapter/course_quiz_screen
files and app.engine.course_status's compute_course_status()/
maybe_award_course_badge() take, instead of each course needing its own
duplicated copy of those 6 screen files + 2 engine functions -- mirrors
the existing app.ui.category_map.CategoryMapFrame(category_filter, heading)
parameterization pattern used for "Build a Project"."""
from __future__ import annotations

from dataclasses import dataclass

from app.engine.categories import AI_COURSE_CATEGORIES, COURSE_CATEGORIES
from app.engine.course_status import COURSE_BADGE_ID


@dataclass(frozen=True)
class CourseSpec:
    id: str
    title: str
    categories: list[str]
    badge_id: str


PYTHON_COURSE = CourseSpec(
    id="python", title="🎓 Python Learning",
    categories=COURSE_CATEGORIES, badge_id=COURSE_BADGE_ID,
)
AI_ML_COURSE = CourseSpec(
    id="ai_ml", title="🤖 AI & Machine Learning",
    categories=AI_COURSE_CATEGORIES, badge_id="ai_ml_graduate",
)
ALL_COURSES = [PYTHON_COURSE, AI_ML_COURSE]


def get_course(course_id: str) -> CourseSpec:
    for course in ALL_COURSES:
        if course.id == course_id:
            return course
    raise KeyError(f"No course registered with id {course_id!r}")


def find_course_for_category(category: str) -> CourseSpec | None:
    for course in ALL_COURSES:
        if category in course.categories:
            return course
    return None
