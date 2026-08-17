"""Main screen: greets the child, shows level/progress, starts today's lesson,
and lists completed missions grouped by category (not one row per lesson --
that grows too long once a category can have dozens of levels) so the child
can jump back into any category they've made progress in.

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
from app.ui.theme_flet import scaled


def build_dashboard_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    return ft.View(
        route="/dashboard",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        # Extra bottom clearance so the last control isn't hidden behind
        # Android's gesture/navigation bar -- see learning_hub_flet.py's
        # build_learning_hub_view() for the full rationale.
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=[
            _build_header(page, state),
            ft.Container(height=16),
            _build_xp_hud(state),
            ft.Container(height=16),
            _build_mission_card(page, state),
            ft.Container(height=16),
            _build_quiz_card(page, state),
            ft.Container(height=16),
            _build_missions_sidebar(page, state),
            ft.Container(height=16),
            ft.Text("More lessons are on their way! 🚀", size=fs(13), color=theme.text_muted),
        ],
    )


def _build_header(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    name = state.settings.child_name or "Explorer"

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Image(src="main-icon.png", width=40, height=40),
                    ft.Text("Python Adventure", size=fs(22), weight=ft.FontWeight.BOLD, color=theme.primary),
                ],
                spacing=8,
            ),
            ft.Row(
                [
                    ft.Button(
                        "🏠 Menu", on_click=lambda _e: page.go("/hub"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                    ft.Button(
                        "📚 Categories", on_click=lambda _e: page.go("/categories"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                    ),
                    ft.Button(
                        "🏆 Trophy Room", on_click=lambda _e: page.go("/trophy-room"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                ],
                spacing=8, wrap=True,
            ),
            ft.Text(f"Welcome back, {name}!", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
        ],
        spacing=10,
    )


def _build_xp_hud(state: AppState) -> ft.Control:
    """Player-level HUD, separate from the existing "Level {n}" stat pill on
    the mission card below (that one is the current lesson's `level` number,
    not an XP-derived player level -- two different, pre-existing meanings
    of "level" in this app, kept visually distinct here rather than
    conflated)."""
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    player = state.progress.get_player_level()
    progress_ratio = player.xp_into_level / player.xp_needed_for_level if player.xp_needed_for_level else 0.0

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(f"LVL {player.level}", size=fs(16), weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    bgcolor=theme.warning, border_radius=10,
                    padding=ft.padding.Padding.symmetric(horizontal=14, vertical=10),
                ),
                ft.Column(
                    [
                        ft.Text("Player Level", size=fs(13), color=theme.text_muted),
                        ft.ProgressBar(
                            value=progress_ratio, color=theme.success, bgcolor=theme.bg,
                            height=14, border_radius=7, width=240,
                        ),
                        ft.Text(f"{player.xp_into_level}/{player.xp_needed_for_level} XP", size=fs(11), color=theme.text_muted),
                    ],
                    spacing=4,
                ),
            ],
            spacing=14,
        ),
        bgcolor=theme.card, border_radius=16, padding=16,
    )


def _build_missions_sidebar(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    engine = state.lesson_engine
    completed_ids = state.progress.get_completed_lesson_ids()
    completion = engine.category_completion(completed_ids)
    started_categories = [(category, done, total) for category, (done, total) in completion.items() if done > 0]

    items: list[ft.Control] = [
        ft.Text("✅ Completed Missions", size=fs(16), weight=ft.FontWeight.BOLD, color=theme.text),
    ]

    if not started_categories:
        items.append(
            ft.Text(
                "Finish your first mission to see it here — then you can jump back into any category!",
                size=fs(12), color=theme.text_muted,
            )
        )
    else:
        chips: list[ft.Control] = []
        for category, done, total in started_categories:
            meta = get_category_meta(category)
            text_color = contrasting_text_color(meta.color)
            status = "✅ All levels complete!" if done == total else f"{done}/{total} completed"
            chips.append(
                ft.Button(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{meta.icon} {meta.title}", size=fs(13), weight=ft.FontWeight.BOLD,
                                color=text_color,
                            ),
                            ft.Text(status, size=fs(12), color=text_color),
                        ],
                        spacing=2,
                    ),
                    on_click=lambda _e, cat=category: page.go(f"/categories/{cat}"),
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
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta("quiz")
    best = state.progress.get_best_quiz_score()
    status = f"🏆 Best: {best[0]}/{best[1]}" if best else f"{len(state.quiz_engine)} questions · Tap to play!"
    text_color = contrasting_text_color(meta.color)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(f"{meta.icon}  Quick Quiz", size=fs(16), weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text(status, size=fs(12), color=text_color),
            ],
            spacing=4,
        ),
        bgcolor=meta.color, border_radius=20, padding=16,
        on_click=lambda _e: page.go("/quiz"),
        ink=True,
    )


def _build_mission_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    summary = state.progress.get_summary()
    engine = state.lesson_engine

    completed_ids = state.progress.get_completed_lesson_ids()
    current_lesson = engine.resolve_current(completed_ids, summary.current_lesson_id)
    already_completed = current_lesson.id in completed_ids

    stats_row = ft.Row(
        [
            _stat_pill(theme, "⭐", f"{summary.total_stars} stars", state.font_scale),
            _stat_pill(theme, "🏆", f"Level {summary.level}", state.font_scale),
            _stat_pill(theme, "🔥", f"{summary.streak_days} day streak", state.font_scale),
            _stat_pill(theme, "🎖️", f"{summary.badges_earned} badges", state.font_scale),
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
                ft.Text("Today's Mission", size=fs(14), color=theme.text_muted),
                ft.Text(current_lesson.title, size=fs(26), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "✅ Completed — replay anytime!" if already_completed else current_lesson.objective,
                    size=fs(14),
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


def _stat_pill(theme, icon: str, text: str, scale: float = 1.0) -> ft.Control:
    return ft.Container(
        content=ft.Text(f"{icon}  {text}", size=scaled(15, scale), color=theme.text),
        bgcolor=theme.bg, border_radius=14, padding=ft.padding.Padding.symmetric(horizontal=14, vertical=8),
    )
