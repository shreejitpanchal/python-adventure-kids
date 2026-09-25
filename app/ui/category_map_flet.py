"""Category browser: pick a topic (Numbers, Addition, ...) laid out as a
winding Adventure Map road -- chunky 3D nodes joined by an S-bend path
that turns the success color as categories are finished, with Codey
floating over the next category to play. Flet only -- CTk keeps its
existing card list (app/ui/category_map.py), per the phase 12 scoping
decision.

Geometry: app/ui/adventure_map_layout.py. Node/road/marker controls:
app/ui/components/map_path_flet.py (shared with category_levels_flet.py).
Every node carries data={"kind": "map_node", ...} for tests.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.categories import get_category_meta
from app.ui.adventure_map_layout import NODE_LIP, NODE_SIZE, PATH_WIDTH, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import emoji_badge, hero_card, hero_header, pill_button, scene_view, spacer
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.map_path_flet import build_map_node, build_you_are_here, node_disc, road_shapes
from app.ui.theme_flet import scaled

_CAPTION_WIDTH = 160.0
DEFAULT_HEADING = "🗺️ Practice by Category"


def codey_map_line(next_title: str | None) -> str:
    if next_title is None:
        return "You've explored every region here! Legendary 🏆"
    return f"Next stop: {next_title}. Tap it to explore!"


def build_category_map_view(
    page: ft.Page, state: AppState,
    category_filter: list[str] | None = None, heading: str | None = None,
) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    engine = state.lesson_engine
    completed_ids = set(state.progress.get_completed_lesson_ids())
    categories = engine.categories()
    if category_filter is not None:
        categories = [category for category in categories if category in category_filter]

    positions = zigzag_positions(len(categories))
    path_height = total_path_height(len(categories))

    done_flags = []
    for category in categories:
        lessons = engine.lessons_in_category(category)
        done_flags.append(bool(lessons) and all(lesson.id in completed_ids for lesson in lessons))
    segment_done = [done_flags[i] and done_flags[i + 1] for i in range(len(categories) - 1)]
    current_index = next((i for i, done in enumerate(done_flags) if not done), None)

    connector_canvas = cv.Canvas(shapes=road_shapes(positions, segment_done, theme))
    stack_children: list[ft.Control] = [
        ft.Container(content=connector_canvas, width=PATH_WIDTH, height=path_height),
    ]
    for index, (category, position) in enumerate(zip(categories, positions)):
        node, caption = _build_node(
            page, theme, category, position, engine, completed_ids, scale, highlight=index == current_index,
        )
        stack_children.extend([node, caption])
        if index == current_index:
            motion.pulse(page, node_disc(node), times=3, big=1.06)
    if current_index is not None:
        stack_children.append(build_you_are_here(positions[current_index], theme, scale, page=page))

    next_title = get_category_meta(categories[current_index]).title if current_index is not None else None
    companion = build_codey_companion(theme, scale, codey_map_line(next_title), page=page)
    header = hero_header(
        theme, title=heading or DEFAULT_HEADING, scale=scale,
        buttons=[pill_button("🏠 Menu", lambda _e: page.go("/hub"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
    )

    quiz_tile = _build_quiz_tile(page, state)
    map_row = ft.Row(
        [ft.Stack(stack_children, width=PATH_WIDTH, height=path_height, data={"kind": "map_stack"})],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    sections: list[ft.Control] = [quiz_tile, map_row]
    for section in sections:
        motion.prepare_entrance(section)

    view = scene_view("/categories", theme, [header, spacer(12), quiz_tile, spacer(12), map_row])
    motion.play_entrance(page, sections)
    return view


def _build_node(page, theme, category, position, engine, completed_ids, scale: float, *, highlight: bool) -> tuple[ft.Control, ft.Control]:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = get_category_meta(category)
    lessons = engine.lessons_in_category(category)
    completed_count = sum(1 for lesson in lessons if lesson.id in completed_ids)
    total = len(lessons)
    all_done = total > 0 and completed_count == total

    def go_to_category(_e: ft.ControlEvent, c: str = category) -> None:
        page.go(f"/categories/{c}")

    node = build_map_node(
        position=position, face=meta.icon, color=meta.color, scale=scale,
        on_click=go_to_category, highlight=highlight,
        data={
            "kind": "map_node", "category": category, "icon": meta.icon, "color": meta.color,
            "completed": completed_count, "total": total, "all_done": all_done,
        },
    )

    status = "✅ All levels complete!" if all_done else f"{completed_count}/{total} levels complete"
    # Clamped, not just centered on the node -- for the leftmost/rightmost
    # zigzag column, a caption centered on the node's x would start left of
    # the Stack's own x=0 (or end past its right edge), clipping the first
    # or last few characters off-screen.
    caption_left = max(0.0, min(position.center_x - _CAPTION_WIDTH / 2, PATH_WIDTH - _CAPTION_WIDTH))
    caption = ft.Container(
        content=ft.Column(
            [
                ft.Text(meta.title, size=fs(12), weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(status, size=fs(11), color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=_CAPTION_WIDTH, left=caption_left, top=position.y + NODE_SIZE + NODE_LIP + 4,
        on_click=go_to_category, ink=True,
        data={"kind": "map_caption", "category": category, "title": meta.title, "status": status},
    )

    return node, caption


def _build_quiz_tile(page: ft.Page, state: AppState) -> ft.Control:
    """The Quiz category isn't derived from lesson content -- it's a
    standalone randomized question bank (app/engine/quiz_engine.py) -- so
    its tile is built directly here instead of from engine.categories(),
    and stays a full-width card above the winding map rather than a node
    on the path, since it isn't part of any lock/unlock sequence and is
    always available."""
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta("quiz")
    best = state.progress.get_best_quiz_score()
    status = f"🏆 Best: {best[0]}/{best[1]}" if best else f"{len(state.quiz_engine)} questions · Not played yet"
    text_color = contrasting_text_color(meta.color)

    return hero_card(
        theme, accent=meta.color,
        children=[
            ft.Row(
                [
                    emoji_badge(meta.icon, size=48, bgcolor=lighten(meta.color, 0.3), scale=state.font_scale),
                    ft.Column(
                        [
                            ft.Text(meta.title, size=fs(17), weight=ft.FontWeight.BOLD, color=text_color),
                            ft.Text(status, size=fs(12), color=text_color),
                        ],
                        spacing=2, expand=True,
                    ),
                ],
                spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        on_click=lambda _e: page.go("/quiz"), padding=16,
        data={"kind": "quiz_tile", "status": status},
    )
