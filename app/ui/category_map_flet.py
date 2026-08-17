"""Category browser: pick a topic (Numbers, Addition, ...) laid out as a
winding Adventure Map path (phase 12) instead of a vertical list of
cards. Flet only -- CTk keeps its existing card list
(app/ui/category_map.py), per the phase 12 scoping decision.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.categories import get_category_meta
from app.ui.adventure_map_layout import NODE_SIZE, PATH_WIDTH, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_CAPTION_WIDTH = 160.0


def build_category_map_view(
    page: ft.Page, state: AppState,
    category_filter: list[str] | None = None, heading: str | None = None,
) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    engine = state.lesson_engine
    completed_ids = set(state.progress.get_completed_lesson_ids())
    categories = engine.categories()
    if category_filter is not None:
        categories = [category for category in categories if category in category_filter]

    positions = zigzag_positions(len(categories))
    path_height = total_path_height(len(categories))

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

    for category, position in zip(categories, positions):
        stack_children.extend(_build_node(page, theme, category, position, engine, completed_ids, state.font_scale))

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/hub"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            # expand=True lets the title wrap onto a second line at large
            # font scales instead of overflowing past the screen edge.
            ft.Text(
                heading or "🗺️ Practice by Category", size=fs(26), weight=ft.FontWeight.BOLD,
                color=theme.primary, expand=True,
            ),
        ],
        spacing=16,
    )

    return ft.View(
        route="/categories",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        # Extra bottom clearance so the last control isn't hidden behind
        # Android's gesture/navigation bar -- see learning_hub_flet.py's
        # build_learning_hub_view() for the full rationale.
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=[
            header,
            _build_quiz_tile(page, state),
            ft.Row([ft.Stack(stack_children, width=PATH_WIDTH, height=path_height)], alignment=ft.MainAxisAlignment.CENTER),
        ],
    )


def _build_node(page, theme, category, position, engine, completed_ids, scale: float) -> list[ft.Control]:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = get_category_meta(category)
    lessons = engine.lessons_in_category(category)
    completed_count = sum(1 for lesson in lessons if lesson.id in completed_ids)
    total = len(lessons)
    all_done = total > 0 and completed_count == total
    node_text_color = contrasting_text_color(meta.color)

    def go_to_category(_e: ft.ControlEvent, c: str = category) -> None:
        page.go(f"/categories/{c}")

    circle = ft.Container(
        content=ft.Text(meta.icon, size=fs(26), text_align=ft.TextAlign.CENTER),
        width=NODE_SIZE, height=NODE_SIZE, border_radius=NODE_SIZE / 2,
        bgcolor=meta.color, alignment=ft.alignment.Alignment.CENTER,
        left=position.x, top=position.y,
        on_click=go_to_category, ink=True,
    )

    status = "✅ All levels complete!" if all_done else f"{completed_count}/{total} levels complete"
    # Clamped, not just centered on the node -- for the leftmost/rightmost
    # zigzag column, a caption centered on the node's x would start left of
    # the Stack's own x=0 (or end past its right edge), clipping the first
    # or last few characters off-screen (reported at "Extra Large" font,
    # but the underlying overflow exists at every font size).
    caption_left = max(0.0, min(position.center_x - _CAPTION_WIDTH / 2, PATH_WIDTH - _CAPTION_WIDTH))
    caption = ft.Container(
        content=ft.Column(
            [
                ft.Text(meta.title, size=fs(12), weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(status, size=fs(11), color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=_CAPTION_WIDTH, left=caption_left, top=position.y + NODE_SIZE + 4,
        on_click=go_to_category, ink=True,
    )

    return [circle, caption]


def _build_quiz_tile(page: ft.Page, state: AppState) -> ft.Control:
    """The Quiz category isn't derived from lesson content -- it's a
    standalone randomized question bank (app/engine/quiz_engine.py) -- so
    its tile is built directly here instead of from engine.categories(),
    and stays a full-width card above the winding map rather than a node
    on the path, since it isn't part of any lock/unlock sequence and is
    always available."""
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta("quiz")
    best = state.progress.get_best_quiz_score()
    status = f"🏆 Best: {best[0]}/{best[1]}" if best else f"{len(state.quiz_engine)} questions · Not played yet"
    text_color = contrasting_text_color(meta.color)

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(meta.icon, size=fs(28)),
                ft.Column(
                    [
                        ft.Text(meta.title, size=fs(18), weight=ft.FontWeight.BOLD, color=text_color),
                        ft.Text(status, size=fs(13), color=text_color),
                    ],
                    spacing=4,
                ),
            ],
            spacing=12,
        ),
        bgcolor=meta.color, border_radius=16, padding=16,
        on_click=lambda _e: page.go("/quiz"),
        ink=True,
    )
