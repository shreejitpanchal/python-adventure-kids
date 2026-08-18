"""The "🎓 Python Learning" course dashboard: an XP/progress-bar header
(styled after dashboard_flet.py's _build_xp_hud/_stat_pill) above a grid of
chapter cards.

Chapters are never locked -- every chapter is always browsable; only the 3
items *within* a chapter gate in order (see course_chapter_flet.py).

Layout note: fixed-width cards in a wrap=True Row, not ft.ResponsiveRow or
expand=True Row children -- see dashboard_flet.py's module docstring for
why expand=True on Row children is avoided in this Flet version.
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.engine.course_status import compute_course_status
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_CARD_WIDTH = 300


def build_course_map_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    status = compute_course_status(state.lesson_engine, state.progress)

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/hub"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text(
                "🎓 Python Learning", size=fs(26), weight=ft.FontWeight.BOLD, color=theme.primary,
                expand=True,
            ),
        ],
        spacing=16,
    )

    return ft.View(
        route="/course",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=[
            header,
            ft.Container(height=16),
            _build_hud(state, status),
            ft.Container(height=16),
            ft.Row(
                [_build_chapter_card(page, state, chapter, index + 1) for index, chapter in enumerate(status.chapters)],
                wrap=True, spacing=16, run_spacing=16,
            ),
        ],
    )


def _build_hud(state: AppState, status) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    ratio = status.items_done / status.items_total if status.items_total else 0.0

    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressBar(value=ratio, color=theme.success, bgcolor=theme.bg, height=18, border_radius=9),
                ft.Text(f"{status.items_done}/{status.items_total} lessons complete", size=fs(12), color=theme.text_muted),
                ft.Row(
                    [
                        _stat_pill(theme, "⭐", f"{status.stars_earned} XP", state.font_scale),
                        _stat_pill(theme, "📘", f"{status.items_done}/{status.items_total} lessons done", state.font_scale),
                        _stat_pill(theme, "📖", f"{len(status.chapters)} chapters", state.font_scale),
                    ],
                    wrap=True, spacing=8, run_spacing=8,
                ),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=16, padding=20,
    )


def _stat_pill(theme, icon: str, text: str, scale: float = 1.0) -> ft.Control:
    return ft.Container(
        content=ft.Text(f"{icon}  {text}", size=scaled(14, scale), color=theme.text),
        bgcolor=theme.bg, border_radius=14, padding=ft.padding.Padding.symmetric(horizontal=14, vertical=8),
    )


def _build_chapter_card(page: ft.Page, state: AppState, chapter, chapter_number: int) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta(chapter.category)
    badge_text_color = contrasting_text_color(meta.color)

    all_done = chapter.completed_count == chapter.total_count
    status_text = "✅ Chapter complete!" if all_done else f"{chapter.completed_count}/{chapter.total_count} items"
    status_color = theme.success if all_done else theme.text_muted

    def on_click(_e: ft.ControlEvent, category: str = chapter.category) -> None:
        page.go(f"/course/{category}")

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(chapter_number), size=fs(16), weight=ft.FontWeight.BOLD, color=badge_text_color),
                            bgcolor=meta.color, border_radius=16, width=32, height=32,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Text(meta.title, size=fs(17), weight=ft.FontWeight.BOLD, color=theme.text, expand=True),
                    ],
                    spacing=10,
                ),
                ft.Text(status_text, size=fs(13), color=status_color),
                ft.Button(
                    "▶ Open Chapter", on_click=on_click, height=38,
                    style=ft.ButtonStyle(bgcolor=meta.color, color=badge_text_color),
                ),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=18, padding=20, width=_CARD_WIDTH,
    )
