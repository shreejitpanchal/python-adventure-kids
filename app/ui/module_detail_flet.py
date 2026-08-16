"""Lessons within one Python Journey module, laid out on the same
winding Adventure Map path as the category browser's level screen
(app/ui/category_levels_flet.py) -- reuses the same
app/ui/adventure_map_layout.py zigzag math. Flet only, matching
journey_map_flet.py's scoping.

Unlock state comes from LearningPathEngine.is_lesson_unlocked() (list
position within the module, not category_level) -- a lesson's actual
category/category_level/main_path/next_lesson_id fields are untouched,
so playing a lesson from here is identical to playing it from anywhere
else; only which lessons are shown and how they're ordered differs.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.learning_path import LearningPathEngine, Module
from app.engine.lesson import Lesson
from app.ui.adventure_map_layout import NODE_SIZE, PATH_WIDTH, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color

_CAPTION_WIDTH = 160.0


def build_module_detail_view(page: ft.Page, state: AppState, module_id: str) -> ft.View:
    theme = state.theme
    learning_path = state.learning_path_engine
    lesson_engine = state.lesson_engine

    if module_id not in {m.id for m in learning_path.modules()}:
        return ft.View(
            route=f"/journey/{module_id}",
            bgcolor=theme.bg,
            controls=[ft.Text(f"Couldn't find module '{module_id}'.", color=theme.danger)],
        )

    module = learning_path.get(module_id)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    stars_by_lesson = state.progress.get_stars_by_lesson()
    lesson_ids = learning_path.module_lesson_ids(module_id)
    lessons = [lesson_engine.get(lesson_id) for lesson_id in lesson_ids]

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
        is_checkpoint = lesson.id == module.checkpoint_lesson_id
        stack_children.extend(
            _build_node(page, theme, learning_path, module, lesson, position, completed_ids, stars_by_lesson, is_checkpoint)
        )

    header = ft.Row(
        [
            ft.Button(
                "🗺️ Journey", on_click=lambda _e: page.go("/journey"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text(f"{module.icon} {module.title}", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )
    description = ft.Text(module.description, size=14, color=theme.text_muted)

    return ft.View(
        route=f"/journey/{module_id}",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[
            header,
            description,
            ft.Row([ft.Stack(stack_children, width=PATH_WIDTH, height=path_height)], alignment=ft.MainAxisAlignment.CENTER),
        ],
    )


def _build_node(
    page: ft.Page, theme, engine: LearningPathEngine, module: Module, lesson: Lesson, position,
    completed_ids: set[str], stars_by_lesson: dict[str, int], is_checkpoint: bool,
) -> list[ft.Control]:
    is_completed = lesson.id in completed_ids
    is_unlocked = engine.is_lesson_unlocked(module.id, lesson.id, completed_ids)
    stars = stars_by_lesson.get(lesson.id, 0)
    enabled = is_completed or is_unlocked

    if is_completed:
        node_color = theme.success
        caption_status = "⭐" * stars if stars else "✅ Completed"
    elif is_unlocked:
        node_color = theme.primary
        caption_status = "🏆 Checkpoint project!" if is_checkpoint else "🔓 Ready to play!"
    else:
        node_color = theme.text_muted
        caption_status = "🔒 Locked"

    node_text_color = contrasting_text_color(node_color)
    node_icon = "🔒" if not enabled else ("🏆" if is_checkpoint else "▶")

    def go_to_lesson(_e: ft.ControlEvent, lesson_id: str = lesson.id) -> None:
        page.go(f"/lesson/{lesson_id}")

    circle = ft.Container(
        content=ft.Text(node_icon, size=22, weight=ft.FontWeight.BOLD, color=node_text_color),
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
