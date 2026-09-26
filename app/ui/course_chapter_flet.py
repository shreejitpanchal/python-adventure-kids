"""One course chapter's items: "1. What is X?", "2. Your Sample Program",
"3. Quiz" -- gated in order within each topic group via
is_topic_item_unlocked() (topic-scoped, so sibling topics like Tuples and
Sets never block each other), laid out as a vertical list of game-world
tiles under topic headings. A chapter with only one implicit topic
(topic="" on every lesson) renders as a flat 3-item list -- no heading.

Control positions are stable for tests: [hero_header, spacer, then topic
heading Rows and item tile Containers]; each tile's Column is [Row(badge,
title), status, button]."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta, get_topic_icon
from app.engine.course_status import compute_course_status, is_topic_item_unlocked
from app.engine.courses import PYTHON_COURSE, CourseSpec
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten
from app.ui.components.adventure_kit_flet import (
    emoji_badge, hero_card, hero_header, pill_button, play_power_bar, power_bar, scene_view, spacer,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.theme_flet import scaled

_ITEM_LABELS = ["1. What is it?", "2. Your Sample Program", "3. Quiz"]


def codey_chapter_line(chapter_title: str, done: int, total: int) -> str:
    if total and done == total:
        return f"{chapter_title}: every item done! On to the next chapter 🎓"
    if done == 0:
        return f"Welcome to {chapter_title}! Start with item 1."
    return f"{done} of {total} done in {chapter_title}. Keep it up!"


def build_course_chapter_view(
    page: ft.Page, state: AppState, category: str, course: CourseSpec = PYTHON_COURSE,
) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = get_category_meta(category)
    status = compute_course_status(state.lesson_engine, state.progress, course.categories)
    chapter = next(c for c in status.chapters if c.category == category)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    map_route = "/course" if course.id == "python" else "/ai-course"
    quiz_route_prefix = "/course-quiz" if course.id == "python" else "/ai-course-quiz"

    ratio = chapter.completed_count / chapter.total_count if chapter.total_count else 0.0
    bar = power_bar(theme, ratio, color=meta.color, width=240, height=12)
    play_power_bar(page, bar)
    companion = build_codey_companion(
        theme, scale, codey_chapter_line(meta.title, chapter.completed_count, chapter.total_count), page=page,
    )
    header = hero_header(
        theme, title=f"{meta.icon} {meta.title}", scale=scale, title_color=meta.color,
        buttons=[pill_button(course.title, lambda _e: page.go(map_route), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=ft.Column([companion.control, bar], spacing=10),
    )

    controls: list[ft.Control] = [header, spacer(12)]
    for topic in chapter.topics:
        if topic.topic:
            icon = get_topic_icon(topic.topic)
            heading = f"{icon} {topic.topic}".strip()
            controls.append(ft.Row(
                [
                    ft.Text(heading, size=fs(18), weight=ft.FontWeight.BOLD, color=meta.color),
                    ft.Text(f"{topic.completed_count}/{topic.total_count}", size=fs(13), color=theme.text_muted),
                ],
                spacing=10,
            ))
        for index, lesson in enumerate(topic.items):
            controls.append(_build_item_card(
                page, theme, meta, lesson, index, topic.items, completed_ids, scale, quiz_route_prefix,
            ))

    return scene_view(f"{map_route}/{category}", theme, controls, page=page)


def _build_item_card(
    page, theme, meta, lesson, index: int, topic_items: list, completed_ids, scale: float,
    quiz_route_prefix: str,
) -> ft.Control:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    is_completed = lesson.id in completed_ids
    is_unlocked = is_topic_item_unlocked(lesson, topic_items, completed_ids)
    label = _ITEM_LABELS[index] if index < len(_ITEM_LABELS) else lesson.title

    if is_completed:
        status_text = "✅ Completed"
        button_text = "▶ REPLAY"
        enabled = True
        accent = theme.star
    elif is_unlocked:
        status_text = "🔓 Ready to play!"
        button_text = "🧩 QUIZ" if lesson.is_quiz else "▶ PLAY"
        enabled = True
        accent = meta.color
    else:
        status_text = "🔒 Locked — finish the item above first"
        button_text = "🔒 LOCKED"
        enabled = False
        accent = theme.text_muted

    text_color = contrasting_text_color(accent)

    def on_click(_e: ft.ControlEvent, lesson_id: str = lesson.id, is_quiz: bool = lesson.is_quiz) -> None:
        page.go(f"{quiz_route_prefix}/{lesson_id}" if is_quiz else f"/lesson/{lesson_id}")

    # Column order [Row(badge, title), status, button] is fixed for tests.
    return hero_card(
        theme, accent=accent, padding=18,
        children=[
            ft.Row(
                [
                    emoji_badge(str(index + 1), size=40, bgcolor=lighten(accent, 0.35), scale=scale, lip=enabled),
                    ft.Text(f"{label} — {lesson.title}", size=fs(17), weight=ft.FontWeight.BOLD, color=text_color, expand=True),
                ],
                spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(status_text, size=fs(14), color=text_color),
            ft.Button(
                button_text, on_click=on_click if enabled else None, disabled=not enabled, height=44, width=160,
                style=ft.ButtonStyle(bgcolor=theme.card if enabled else theme.text_muted, color=theme.text if enabled else "#FFFFFF"),
            ),
        ],
        data={"kind": "chapter_item", "lesson_id": lesson.id, "completed": is_completed, "unlocked": is_unlocked},
    )
