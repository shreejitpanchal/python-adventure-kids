"""Category browser: pick a topic (Numbers, Addition, ...) to see its levels."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color


def build_category_map_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    engine = state.lesson_engine
    completed_ids = set(state.progress.get_completed_lesson_ids())

    items: list[ft.Control] = []
    for category in engine.categories():
        lessons = engine.lessons_in_category(category)
        meta = get_category_meta(category)
        completed_count = sum(1 for lesson in lessons if lesson.id in completed_ids)
        total = len(lessons)
        all_done = completed_count == total
        status = "✅ All levels complete!" if all_done else f"{completed_count}/{total} levels complete"
        text_color = contrasting_text_color(meta.color)

        items.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"{meta.icon}  {meta.title}", size=18, weight=ft.FontWeight.BOLD, color=text_color),
                        ft.Text(status, size=13, color=text_color),
                    ],
                    spacing=4,
                ),
                bgcolor=meta.color, border_radius=16, padding=16,
                on_click=lambda _e, c=category: page.go(f"/categories/{c}"),
                ink=True,
            )
        )

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"),
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text("🗺️ Practice by Category", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )

    return ft.View(
        route="/categories",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[header, ft.Column(items, spacing=8)],
    )
