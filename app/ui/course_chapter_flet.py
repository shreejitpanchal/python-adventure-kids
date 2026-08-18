"""One course chapter's items: "1. What is X?", "2. Your Sample Program",
"3. Quiz" -- gated in order within each topic group via
is_topic_item_unlocked() (topic-scoped, so sibling topics like Tuples and
Sets never block each other), laid out as a plain vertical Column of item
cards (dashboard-card style, not the zigzag adventure-map path). A chapter
with only one implicit topic (topic="" on every lesson) renders
identically to a flat 3-item list -- no topic heading shown."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta, get_topic_icon
from app.engine.course_status import compute_course_status, is_topic_item_unlocked
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_ITEM_LABELS = ["1. What is it?", "2. Your Sample Program", "3. Quiz"]


def build_course_chapter_view(page: ft.Page, state: AppState, category: str) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta(category)
    status = compute_course_status(state.lesson_engine, state.progress)
    chapter = next(c for c in status.chapters if c.category == category)
    completed_ids = set(state.progress.get_completed_lesson_ids())

    header = ft.Row(
        [
            ft.Button(
                "🎓 Python Learning", on_click=lambda _e: page.go("/course"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text(f"{meta.icon} {meta.title}", size=fs(24), weight=ft.FontWeight.BOLD, color=meta.color, expand=True),
        ],
        spacing=16,
    )

    controls: list[ft.Control] = [header, ft.Container(height=16)]
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
            controls.append(_build_item_card(page, theme, meta, lesson, index, topic.items, completed_ids, state.font_scale))

    return ft.View(
        route=f"/course/{category}",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=controls,
    )


def _build_item_card(page, theme, meta, lesson, index: int, topic_items: list, completed_ids, scale: float) -> ft.Control:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    is_completed = lesson.id in completed_ids
    is_unlocked = is_topic_item_unlocked(lesson, topic_items, completed_ids)
    label = _ITEM_LABELS[index] if index < len(_ITEM_LABELS) else lesson.title

    if is_completed:
        status_text = "✅ Completed"
        button_text = "▶ REPLAY"
        enabled = True
    elif is_unlocked:
        status_text = "🔓 Ready to play!"
        button_text = "🧩 QUIZ" if lesson.is_quiz else "▶ PLAY"
        enabled = True
    else:
        status_text = "🔒 Locked — finish the item above first"
        button_text = "🔒 LOCKED"
        enabled = False

    status_color = theme.success if is_completed else (theme.primary if is_unlocked else theme.text_muted)
    badge_text_color = contrasting_text_color(meta.color)

    def on_click(_e: ft.ControlEvent, lesson_id: str = lesson.id, is_quiz: bool = lesson.is_quiz) -> None:
        page.go(f"/course-quiz/{lesson_id}" if is_quiz else f"/lesson/{lesson_id}")

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(index + 1), size=fs(16), weight=ft.FontWeight.BOLD, color=badge_text_color),
                            bgcolor=meta.color, border_radius=16, width=32, height=32,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Text(f"{label} — {lesson.title}", size=fs(17), weight=ft.FontWeight.BOLD, color=theme.text, expand=True),
                    ],
                    spacing=10,
                ),
                ft.Text(status_text, size=fs(14), color=status_color),
                ft.Button(
                    button_text, on_click=on_click if enabled else None, disabled=not enabled, height=44, width=160,
                    style=ft.ButtonStyle(bgcolor=theme.success if enabled else theme.text_muted, color="#FFFFFF"),
                ),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=16, padding=20,
    )
