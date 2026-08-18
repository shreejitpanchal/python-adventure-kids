"""One course chapter's 3 items: "1. What is X?", "2. Your Sample Program",
"3. Quiz" -- gated in order via the same LessonEngine.is_unlocked() used by
category_levels_flet.py, laid out as a plain vertical Column of item cards
(dashboard-card style, not the zigzag adventure-map path)."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_ITEM_LABELS = ["1. What is it?", "2. Your Sample Program", "3. Quiz"]


def build_course_chapter_view(page: ft.Page, state: AppState, category: str) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    engine = state.lesson_engine
    meta = get_category_meta(category)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    lessons = engine.lessons_in_category(category)

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

    items = [
        _build_item_card(page, theme, meta, lesson, index, engine, completed_ids, state.font_scale)
        for index, lesson in enumerate(lessons)
    ]

    return ft.View(
        route=f"/course/{category}",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=[header, ft.Container(height=16), *items],
    )


def _build_item_card(page, theme, meta, lesson, index: int, engine, completed_ids, scale: float) -> ft.Control:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    is_completed = lesson.id in completed_ids
    is_unlocked = engine.is_unlocked(lesson, completed_ids)
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
