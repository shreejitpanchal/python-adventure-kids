"""Main screen: greets the child, shows level/progress, starts today's lesson,
and lists completed missions so the child can replay any of them.

Layout note: `expand=True` on Row children currently renders incorrectly in
this Flet version (first child consumes all space, siblings vanish --
verified in isolation, not specific to this screen). Until that's resolved
or worked around, this screen stacks sections vertically in a Column
rather than using side-by-side Rows/ResponsiveRow -- which also suits a
tablet-first layout better anyway, so revisit only if desktop wants a
wider two-column look during the Phase 8 UX pass."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color


def build_dashboard_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme

    return ft.View(
        route="/dashboard",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[
            _build_header(page, state),
            ft.Container(height=16),
            _build_mission_card(page, state),
            ft.Container(height=16),
            _build_missions_sidebar(page, state),
            ft.Container(height=16),
            _build_quiz_card(page, state),
            ft.Container(height=16),
            ft.Text("More lessons are on their way! 🚀", size=13, color=theme.text_muted),
        ],
    )


def _build_header(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    name = state.settings.child_name or "Explorer"

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Image(src="main-icon.png", width=40, height=40),
                    ft.Text("Python Adventure", size=22, weight=ft.FontWeight.BOLD, color=theme.primary),
                ],
                spacing=8,
            ),
            ft.Row(
                [
                    ft.Button(
                        "🗺️ Categories", on_click=lambda _e: page.go("/categories"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                    ),
                    ft.Button(
                        "⚙️ Settings", on_click=lambda _e: page.go("/settings"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                    ft.Button(
                        "👋 Parent Area", on_click=lambda _e: page.go("/parent"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                ],
                spacing=8, wrap=True,
            ),
            ft.Text(f"Welcome back, {name}!", size=20, weight=ft.FontWeight.BOLD, color=theme.text),
        ],
        spacing=10,
    )


def _build_missions_sidebar(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    engine = state.lesson_engine
    completed_ids = set(state.progress.get_completed_lesson_ids())
    stars_by_lesson = state.progress.get_stars_by_lesson()
    completed_lessons = [lesson for lesson in engine.all_in_order() if lesson.id in completed_ids]

    items: list[ft.Control] = [
        ft.Text("✅ Completed Missions", size=16, weight=ft.FontWeight.BOLD, color=theme.text),
    ]

    if not completed_lessons:
        items.append(
            ft.Text(
                "Finish your first mission to see it here — then you can replay it anytime!",
                size=12, color=theme.text_muted,
            )
        )
    else:
        chips: list[ft.Control] = []
        for lesson in completed_lessons:
            stars = stars_by_lesson.get(lesson.id, 0)
            meta = get_category_meta(lesson.category)
            text_color = contrasting_text_color(meta.color)
            chips.append(
                ft.Button(
                    content=ft.Column(
                        [
                            ft.Text(lesson.title, size=13, color=text_color),
                            ft.Text("⭐" * stars if stars else " ", size=13, color=text_color),
                        ],
                        spacing=2,
                    ),
                    on_click=lambda _e, lesson_id=lesson.id: page.go(f"/lesson/{lesson_id}"),
                    style=ft.ButtonStyle(bgcolor=meta.color),
                )
            )
        items.append(ft.Row(chips, wrap=True, spacing=8, run_spacing=8))

    return ft.Container(
        content=ft.Column(items, spacing=8),
        bgcolor=theme.card, border_radius=20, padding=16,
    )


def _build_quiz_card(page: ft.Page, state: AppState) -> ft.Control:
    """Same tile pattern as the Quiz entry in the category browser
    (category_map_flet.py's _build_quiz_tile) -- a quick-access shortcut
    to the same standalone quiz, not a lesson category."""
    meta = get_category_meta("quiz")
    best = state.progress.get_best_quiz_score()
    status = f"🏆 Best: {best[0]}/{best[1]}" if best else f"{len(state.quiz_engine)} questions · Tap to play!"
    text_color = contrasting_text_color(meta.color)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(f"{meta.icon}  Quick Quiz", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text(status, size=12, color=text_color),
            ],
            spacing=4,
        ),
        bgcolor=meta.color, border_radius=20, padding=16,
        on_click=lambda _e: page.go("/quiz"),
        ink=True,
    )


def _build_mission_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    summary = state.progress.get_summary()
    engine = state.lesson_engine

    completed_ids = state.progress.get_completed_lesson_ids()
    current_lesson = engine.resolve_current(completed_ids, summary.current_lesson_id)
    already_completed = current_lesson.id in completed_ids

    stats_row = ft.Row(
        [
            _stat_pill(theme, "⭐", f"{summary.total_stars} stars"),
            _stat_pill(theme, "🏆", f"Level {summary.level}"),
            _stat_pill(theme, "🔥", f"{summary.streak_days} day streak"),
            _stat_pill(theme, "🎖️", f"{summary.badges_earned} badges"),
        ],
        wrap=True,
    )

    total_lessons = max(len(engine.main_path_lessons()), 1)
    progress_bar = ft.ProgressBar(
        value=min(summary.lessons_completed / total_lessons, 1.0),
        color=theme.star, bgcolor=theme.bg, height=18, border_radius=9,
    )

    button_text = "▶ REPLAY" if already_completed else "▶ CONTINUE"

    return ft.Container(
        content=ft.Column(
            [
                stats_row,
                ft.Text("Today's Mission", size=14, color=theme.text_muted),
                ft.Text(current_lesson.title, size=26, weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "✅ Completed — replay anytime!" if already_completed else current_lesson.objective,
                    size=14,
                    color=theme.success if already_completed else theme.text_muted,
                ),
                progress_bar,
                ft.Button(
                    button_text, width=280, height=64,
                    on_click=lambda _e: page.go(f"/lesson/{current_lesson.id}"),
                    style=ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF"),
                ),
            ],
            spacing=12,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _stat_pill(theme, icon: str, text: str) -> ft.Control:
    return ft.Container(
        content=ft.Text(f"{icon}  {text}", size=15, color=theme.text),
        bgcolor=theme.bg, border_radius=14, padding=ft.padding.Padding.symmetric(horizontal=14, vertical=8),
    )
