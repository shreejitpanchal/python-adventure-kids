"""Python Journey: the 8-module course map, laid out on the same winding
Adventure Map path as the category browser (app/ui/category_map_flet.py)
-- reuses app/ui/adventure_map_layout.py's zigzag math as-is. Flet only,
matching every other new UI surface built this session (Arcade Lab,
Robot Adventure, the category Adventure Map itself) -- CTk keeps its flat
dashboard/category browser, sharing only the underlying engine/badge
logic (app/engine/learning_path.py, the module-badge award hook in both
lesson_screen.py and lesson_screen_flet.py).
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.learning_path import LearningPathEngine, Module, ModuleStatus
from app.ui.adventure_map_layout import NODE_SIZE, PATH_WIDTH, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color

_CAPTION_WIDTH = 160.0

_STATUS_LABELS: dict[ModuleStatus, str] = {
    "locked": "🔒 Locked",
    "available": "🔓 Ready to start!",
    "in_progress": "▶ In progress",
    "completed": "✅ Completed!",
}


def build_journey_map_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    engine = state.learning_path_engine
    completed_ids = set(state.progress.get_completed_lesson_ids())

    # The migration-free "catch up" check -- see
    # LearningPathEngine.newly_earned_module_badges()'s docstring. Runs
    # every time this screen loads; award_badge() is idempotent so
    # re-checking already-awarded modules is cheap and harmless.
    already_awarded = state.progress.get_badge_ids()
    for badge_id in engine.newly_earned_module_badges(completed_ids, already_awarded):
        state.progress.award_badge(badge_id)

    modules = engine.modules()
    positions = zigzag_positions(len(modules))
    path_height = total_path_height(len(modules))

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
    for module, position in zip(modules, positions):
        stack_children.extend(_build_node(page, theme, engine, module, position, completed_ids))

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text("🗺️ Python Journey", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )

    current = engine.current_module(completed_ids)
    modules_done, modules_total = engine.progress_summary(completed_ids)
    lessons_completed = len(completed_ids)
    progress_text = ft.Text(
        f"Module {current.order} of {modules_total} — {modules_done} module"
        f"{'s' if modules_done != 1 else ''} completed · {lessons_completed} lessons completed",
        size=14, color=theme.text_muted,
    )

    return ft.View(
        route="/journey",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[
            header,
            progress_text,
            ft.Row([ft.Stack(stack_children, width=PATH_WIDTH, height=path_height)], alignment=ft.MainAxisAlignment.CENTER),
        ],
    )


def _build_node(
    page: ft.Page, theme, engine: LearningPathEngine, module: Module, position, completed_ids: set[str],
) -> list[ft.Control]:
    status = engine.module_status(module.id, completed_ids)
    color = {
        "locked": theme.text_muted,
        "available": theme.primary,
        "in_progress": theme.warning,
        "completed": theme.success,
    }[status]
    enabled = status != "locked"
    node_text_color = contrasting_text_color(color)

    def go_to_module(_e: ft.ControlEvent, module_id: str = module.id) -> None:
        page.go(f"/journey/{module_id}")

    circle = ft.Container(
        content=ft.Text(module.icon if enabled else "🔒", size=26, text_align=ft.TextAlign.CENTER),
        width=NODE_SIZE, height=NODE_SIZE, border_radius=NODE_SIZE / 2,
        bgcolor=color, alignment=ft.alignment.Alignment.CENTER,
        left=position.x, top=position.y,
        on_click=go_to_module if enabled else None, ink=enabled,
    )

    caption = ft.Container(
        content=ft.Column(
            [
                ft.Text(module.title, size=12, weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(_STATUS_LABELS[status], size=11, color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=_CAPTION_WIDTH, left=position.center_x - _CAPTION_WIDTH / 2, top=position.y + NODE_SIZE + 4,
        on_click=go_to_module if enabled else None, ink=enabled,
    )

    return [circle, caption]
