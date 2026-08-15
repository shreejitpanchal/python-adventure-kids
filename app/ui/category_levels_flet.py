"""Levels within one category, laid out as a winding Adventure Map path
(phase 12) instead of a vertical list of cards: play the next unlocked
node, replay a completed one, or see upcoming nodes locked until the one
before them is finished. Flet only -- CTk keeps its existing card list
(app/ui/category_levels.py), per the phase 12 scoping decision.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.categories import get_category_meta
from app.ui.adventure_map_layout import NODE_SIZE, PATH_WIDTH, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color

_CAPTION_WIDTH = 160.0


def build_category_levels_view(page: ft.Page, state: AppState, category: str) -> ft.View:
    theme = state.theme
    engine = state.lesson_engine
    meta = get_category_meta(category)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    stars_by_lesson = state.progress.get_stars_by_lesson()
    lessons = engine.lessons_in_category(category)

    positions = zigzag_positions(len(lessons))
    path_height = total_path_height(len(lessons))

    connector_canvas = cv.Canvas(
        shapes=[
            cv.Line(
                positions[i].center_x, positions[i].center_y,
                positions[i + 1].center_x, positions[i + 1].center_y,
                paint=ft.Paint(color=theme.text_muted, stroke_width=4),
            )
            for i in range(len(positions) - 1)
        ],
    )
    stack_children: list[ft.Control] = [
        ft.Container(content=connector_canvas, width=PATH_WIDTH, height=path_height),
    ]

    for lesson, position in zip(lessons, positions):
        stack_children.extend(
            _build_node(page, theme, meta, lesson, position, completed_ids, stars_by_lesson, engine)
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
        controls=[
            header,
            ft.Row([ft.Stack(stack_children, width=PATH_WIDTH, height=path_height)], alignment=ft.MainAxisAlignment.CENTER),
        ],
    )


def _build_node(page, theme, meta, lesson, position, completed_ids, stars_by_lesson, engine) -> list[ft.Control]:
    is_completed = lesson.id in completed_ids
    is_unlocked = engine.is_unlocked(lesson, completed_ids)
    stars = stars_by_lesson.get(lesson.id, 0)
    enabled = is_completed or is_unlocked

    if is_completed:
        node_color = theme.success
        caption_status = "⭐" * stars if stars else "✅ Completed"
    elif is_unlocked:
        node_color = meta.color
        caption_status = "🔓 Ready to play!"
    else:
        node_color = theme.text_muted
        caption_status = "🔒 Locked"

    node_text_color = contrasting_text_color(node_color)

    def go_to_lesson(_e: ft.ControlEvent, lesson_id: str = lesson.id) -> None:
        page.go(f"/lesson/{lesson_id}")

    circle = ft.Container(
        content=ft.Text(
            "🔒" if not enabled else str(lesson.category_level),
            size=22, weight=ft.FontWeight.BOLD, color=node_text_color,
        ),
        width=NODE_SIZE, height=NODE_SIZE, border_radius=NODE_SIZE / 2,
        bgcolor=node_color, alignment=ft.alignment.Alignment.CENTER,
        left=position.x, top=position.y,
        on_click=go_to_lesson if enabled else None,
        ink=enabled,
    )

    caption = ft.Container(
        content=ft.Column(
            [
                ft.Text(lesson.title, size=12, weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(caption_status, size=11, color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=_CAPTION_WIDTH, left=position.center_x - _CAPTION_WIDTH / 2, top=position.y + NODE_SIZE + 4,
        on_click=go_to_lesson if enabled else None,
        ink=enabled,
    )

    return [circle, caption]
