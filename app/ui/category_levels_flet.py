"""Levels within one category: play the next unlocked level, replay a completed
one, or see upcoming levels locked until the one before them is finished."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color


def build_category_levels_view(page: ft.Page, state: AppState, category: str) -> ft.View:
    theme = state.theme
    engine = state.lesson_engine
    meta = get_category_meta(category)
    badge_text_color = contrasting_text_color(meta.color)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    stars_by_lesson = state.progress.get_stars_by_lesson()
    lessons = engine.lessons_in_category(category)

    cards: list[ft.Control] = []
    for lesson in lessons:
        is_completed = lesson.id in completed_ids
        is_unlocked = engine.is_unlocked(lesson, completed_ids)
        stars = stars_by_lesson.get(lesson.id, 0)

        if is_completed:
            status_text = f"✅ Completed  {'⭐' * stars}"
            status_color = theme.success
            button_text = "▶ REPLAY"
            enabled = True
        elif is_unlocked:
            status_text = "🔓 Ready to play!"
            status_color = theme.primary
            button_text = "▶ PLAY"
            enabled = True
        else:
            status_text = "🔒 Locked — finish the level above first"
            status_color = theme.text_muted
            button_text = "🔒 LOCKED"
            enabled = False

        badge = ft.Container(
            content=ft.Text(str(lesson.category_level), size=16, weight=ft.FontWeight.BOLD, color=badge_text_color),
            bgcolor=meta.color, border_radius=16, width=32, height=32, alignment=ft.alignment.Alignment.CENTER,
        )

        cards.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([badge, ft.Text(lesson.title, size=18, weight=ft.FontWeight.BOLD, color=theme.text)],
                               spacing=10),
                        ft.Text(status_text, size=14, color=status_color),
                        ft.Button(
                            button_text, width=160, height=48, disabled=not enabled,
                            on_click=lambda _e, lesson_id=lesson.id: page.go(f"/lesson/{lesson_id}"),
                            style=ft.ButtonStyle(
                                bgcolor=theme.success if enabled else theme.text_muted, color="#FFFFFF",
                            ),
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=theme.card, border_radius=16, padding=20,
            )
        )

    header = ft.Row(
        [
            ft.Button(
                "🗺️ Categories", on_click=lambda _e: page.go("/categories"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text(f"{meta.icon} {meta.title}", size=26, weight=ft.FontWeight.BOLD, color=meta.color),
        ],
        spacing=16,
    )

    return ft.View(
        route=f"/categories/{category}",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[header, ft.Column(cards, spacing=8)],
    )
