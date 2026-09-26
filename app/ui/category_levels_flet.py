"""Levels within one category, laid out as a winding Adventure Map road:
play the next unlocked node (Codey floats above it), replay a completed
one (gold, with its stars in the caption), or see upcoming nodes locked
until the one before them is finished. Flet only -- CTk keeps its
existing card list (app/ui/category_levels.py), per the phase 12 scoping
decision.

Geometry: app/ui/adventure_map_layout.py. Node/road/marker controls:
app/ui/components/map_path_flet.py (shared with category_map_flet.py).
Every node carries data={"kind": "map_node", "state": ...} for tests.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.categories import get_category_meta
from app.engine.worlds import world_for_category
from app.ui.adventure_map_layout import NODE_LIP, NODE_SIZE, total_path_height, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    hero_header, layout_for, pill_button, plain_card, play_power_bar, power_bar, scene_view, spacer,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.map_path_flet import build_map_node, build_you_are_here, node_disc, road_shapes
from app.ui.theme_flet import scaled

_CAPTION_WIDTH = 160.0

LOCKED = "locked"
UNLOCKED = "unlocked"
COMPLETED = "completed"


def codey_levels_line(category_title: str, done: int, total: int, next_title: str | None) -> str:
    if total and done == total:
        return f"{category_title} conquered! Every level done ⭐"
    if next_title is None:
        return f"Welcome to {category_title}!"
    return f"Up next: {next_title}. Let's go!"


def build_category_levels_view(page: ft.Page, state: AppState, category: str) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    fs = lambda base: scaled(base, scale)  # noqa: E731
    layout = layout_for(page)
    engine = state.lesson_engine
    meta = get_category_meta(category)
    world = world_for_category(category)
    completed_ids = set(state.progress.get_completed_lesson_ids())
    stars_by_lesson = state.progress.get_stars_by_lesson()
    lessons = engine.lessons_in_category(category)

    positions = zigzag_positions(len(lessons), lanes=layout.map_lanes, path_width=layout.map_width)
    path_height = total_path_height(len(lessons))

    states = [_lesson_state(lesson, completed_ids, engine) for lesson in lessons]
    segment_done = [states[i] == COMPLETED and states[i + 1] == COMPLETED for i in range(len(lessons) - 1)]
    current_index = next((i for i, lesson_state in enumerate(states) if lesson_state == UNLOCKED), None)

    connector_canvas = cv.Canvas(shapes=road_shapes(positions, segment_done, theme))
    stack_children: list[ft.Control] = [
        ft.Container(content=connector_canvas, width=layout.map_width, height=path_height),
    ]
    for index, (lesson, position, lesson_state) in enumerate(zip(lessons, positions, states)):
        node, caption = _build_node(
            page, theme, meta, lesson, position, lesson_state, stars_by_lesson, scale, layout.map_width,
            highlight=index == current_index,
        )
        stack_children.extend([node, caption])
        if index == current_index:
            motion.pulse(page, node_disc(node), times=3, big=1.06)
    if current_index is not None:
        stack_children.append(build_you_are_here(positions[current_index], theme, scale, page=page))

    done_count = sum(1 for lesson_state in states if lesson_state == COMPLETED)
    next_title = lessons[current_index].title if current_index is not None else None
    companion = build_codey_companion(
        theme, scale, codey_levels_line(meta.title, done_count, len(lessons), next_title), page=page,
    )
    header = hero_header(
        theme, title=f"{meta.icon} {meta.title}", scale=scale, title_color=meta.color,
        buttons=[pill_button("🗺️ Categories", lambda _e: page.go("/categories"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
    )

    ratio = done_count / len(lessons) if lessons else 0.0
    progress_bar = power_bar(theme, ratio, color=meta.color, width=260, height=14)
    play_power_bar(page, progress_bar)
    progress_card = plain_card(
        theme,
        [
            ft.Text(f"{world.icon} {world.title}", size=fs(12), color=theme.text_muted),
            ft.Text(f"{done_count}/{len(lessons)} levels complete", size=fs(14), weight=ft.FontWeight.BOLD, color=theme.text),
            progress_bar,
        ],
        data={"kind": "category_progress", "done": done_count, "total": len(lessons), "world": world.id},
    )

    map_row = ft.Row(
        [ft.Stack(stack_children, width=layout.map_width, height=path_height, data={"kind": "map_stack"})],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    sections: list[ft.Control] = [progress_card, map_row]
    for section in sections:
        motion.prepare_entrance(section)

    view = scene_view(
        f"/categories/{category}", theme, [header, spacer(12), progress_card, spacer(12), map_row], page=page,
    )
    motion.play_entrance(page, sections)
    return view


def _lesson_state(lesson, completed_ids, engine) -> str:
    if lesson.id in completed_ids:
        return COMPLETED
    if engine.is_unlocked(lesson, completed_ids):
        return UNLOCKED
    return LOCKED


def _build_node(
    page, theme, meta, lesson, position, lesson_state: str, stars_by_lesson, scale: float, path_width: float,
    *, highlight: bool,
) -> tuple[ft.Control, ft.Control]:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    stars = stars_by_lesson.get(lesson.id, 0)
    enabled = lesson_state != LOCKED

    if lesson_state == COMPLETED:
        node_color = theme.star
        caption_status = "⭐" * stars if stars else "✅ Completed"
    elif lesson_state == UNLOCKED:
        node_color = meta.color
        caption_status = "🔓 Ready to play!"
    else:
        node_color = theme.text_muted
        caption_status = "🔒 Locked"

    label = "🔒" if not enabled else str(lesson.category_level)

    def go_to_lesson(_e: ft.ControlEvent, lesson_id: str = lesson.id) -> None:
        page.go(f"/lesson/{lesson_id}")

    node = build_map_node(
        position=position, face=label, color=node_color, scale=scale, face_size=24,
        on_click=go_to_lesson if enabled else None, dim=not enabled, highlight=highlight,
        data={
            "kind": "map_node", "lesson_id": lesson.id, "label": label, "state": lesson_state,
            "color": node_color, "stars": stars,
        },
    )

    # Clamped, not just centered on the node -- see category_map_flet.py.
    caption_left = max(0.0, min(position.center_x - _CAPTION_WIDTH / 2, path_width - _CAPTION_WIDTH))
    caption = ft.Container(
        content=ft.Column(
            [
                ft.Text(lesson.title, size=fs(12), weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(caption_status, size=fs(11), color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=_CAPTION_WIDTH, left=caption_left, top=position.y + NODE_SIZE + NODE_LIP + 4,
        on_click=go_to_lesson if enabled else None,
        ink=enabled,
        data={"kind": "map_caption", "lesson_id": lesson.id, "title": lesson.title, "status": caption_status},
    )

    return node, caption
