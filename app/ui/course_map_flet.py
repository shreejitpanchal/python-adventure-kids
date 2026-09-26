"""A course dashboard (e.g. "🎓 Python Learning" or "🤖 AI & Machine
Learning" -- see app.engine.courses.CourseSpec): a progress HUD above a
grid of chapter tiles, styled with the game-world kit.

Chapters are never locked -- every chapter is always browsable; only the 3
items *within* a chapter gate in order (see course_chapter_flet.py).

Control positions are stable for tests: [hero_header, spacer, hud, spacer,
Row(chapter tiles)]; each tile's Column is [Row(badge, title), status,
button].
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.engine.course_status import compute_course_status
from app.engine.courses import PYTHON_COURSE, CourseSpec
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    emoji_badge, hero_card, hero_header, pill_button, plain_card, play_power_bar, power_bar, scene_view, spacer,
    stat_chip,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.theme_flet import scaled

_CARD_WIDTH = 300


def codey_course_line(done: int, total: int, course_title: str) -> str:
    if total and done == total:
        return f"{course_title} complete — you're a graduate! 🎓"
    if done == 0:
        return "A whole course to explore. Open Chapter 1 to begin!"
    return f"{done} of {total} lessons done. Pick a chapter and keep going!"


def build_course_map_view(page: ft.Page, state: AppState, course: CourseSpec = PYTHON_COURSE) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    status = compute_course_status(state.lesson_engine, state.progress, course.categories)
    route_prefix = "/course" if course.id == "python" else "/ai-course"

    companion = build_codey_companion(
        theme, scale, codey_course_line(status.items_done, status.items_total, course.title), page=page,
    )
    header = hero_header(
        theme, title=course.title, scale=scale,
        buttons=[pill_button("🏠 Menu", lambda _e: page.go("/hub"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
    )

    hud = _build_hud(page, state, status)
    grid = ft.Row(
        [
            _build_chapter_card(page, route_prefix, state, chapter, index + 1)
            for index, chapter in enumerate(status.chapters)
        ],
        wrap=True, spacing=16, run_spacing=16,
    )
    for section in (hud, grid):
        motion.prepare_entrance(section)

    view = scene_view(route_prefix, theme, [header, spacer(12), hud, spacer(12), grid], page=page)
    motion.play_entrance(page, [hud, grid])
    return view


def _build_hud(page: ft.Page, state: AppState, status) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    ratio = status.items_done / status.items_total if status.items_total else 0.0
    bar = power_bar(theme, ratio, color=theme.success, width=260, height=16)
    play_power_bar(page, bar)

    # Column order [bar, lessons text, chips] is fixed for tests.
    return plain_card(
        theme,
        [
            bar,
            ft.Text(f"{status.items_done}/{status.items_total} lessons complete", size=fs(12), color=theme.text_muted),
            ft.Row(
                [
                    stat_chip(theme, "⭐", f"{status.stars_earned} XP", state.font_scale),
                    stat_chip(theme, "📘", f"{status.items_done}/{status.items_total} lessons done", state.font_scale),
                    stat_chip(theme, "📖", f"{len(status.chapters)} chapters", state.font_scale),
                ],
                wrap=True, spacing=8, run_spacing=8,
            ),
        ],
        padding=20, spacing=8,
        data={"kind": "course_hud", "done": status.items_done, "total": status.items_total},
    )


def _build_chapter_card(page: ft.Page, route_prefix: str, state: AppState, chapter, chapter_number: int) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta(chapter.category)
    text_color = contrasting_text_color(meta.color)

    all_done = chapter.completed_count == chapter.total_count
    status_text = "✅ Chapter complete!" if all_done else f"{chapter.completed_count}/{chapter.total_count} items"

    def on_click(_e: ft.ControlEvent, category: str = chapter.category) -> None:
        page.go(f"{route_prefix}/{category}")

    # Column order [Row(badge, title), status, button] is fixed for tests.
    return hero_card(
        theme, accent=meta.color, width=_CARD_WIDTH, padding=18,
        children=[
            ft.Row(
                [
                    emoji_badge(str(chapter_number), size=40, bgcolor=lighten(meta.color, 0.35), scale=state.font_scale),
                    ft.Text(meta.title, size=fs(17), weight=ft.FontWeight.BOLD, color=text_color, expand=True),
                ],
                spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(status_text, size=fs(13), color=text_color),
            ft.Button(
                "▶ Open Chapter", on_click=on_click, height=40,
                style=ft.ButtonStyle(bgcolor=theme.card, color=theme.text),
            ),
        ],
        data={"kind": "chapter_card", "category": chapter.category, "complete": all_done},
    )
