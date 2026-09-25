"""Today's Mission screen: Codey introduces the current mission, the XP
power bar shows the player level, a big gradient mission tile with a
chunky CONTINUE button starts today's lesson, and completed missions are
listed grouped by category (not one row per lesson -- that grows too
long once a category can have dozens of levels) so the child can jump
back into any category they've made progress in.

Visuals come from app/ui/components/adventure_kit_flet.py. Key controls
carry data={"kind": ...} for tests (see adventure_kit_flet.find_by_kind)
instead of relying on positional indexes.

Layout note: sections stack vertically in a Column -- tablet/phone-first,
and `expand=True` is only used on the single Text/Column inside a Row
(the pattern every header here already relies on)."""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    RADIUS_PILL, emoji_badge, hero_card, hero_header, pill_button, plain_card, play_power_bar, power_bar,
    scene_view, spacer,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.game_button_flet import build_game_button
from app.ui.theme_flet import scaled


def codey_mission_line(lesson_title: str, already_completed: bool) -> str:
    if already_completed:
        return "Mission complete! Replay it, or pick a new level on the map 🎯"
    return f"Today's mission: {lesson_title}. You've got this!"


def build_dashboard_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    fs = lambda base: scaled(base, scale)  # noqa: E731
    engine = state.lesson_engine
    summary = state.progress.get_summary()
    completed_ids = state.progress.get_completed_lesson_ids()
    current_lesson = engine.resolve_current(completed_ids, summary.current_lesson_id)
    already_completed = current_lesson.id in completed_ids

    companion = build_codey_companion(
        theme, scale, codey_mission_line(current_lesson.title, already_completed), page=page,
    )
    header = hero_header(
        theme, title="Today's Mission", scale=scale,
        buttons=[
            pill_button("🏠 Menu", lambda _e: page.go("/hub"), bgcolor=theme.text_muted, color="#FFFFFF"),
            pill_button("🗺️ Adventure Map", lambda _e: page.go("/categories"), bgcolor=theme.primary),
            pill_button("🏆 Trophy Room", lambda _e: page.go("/trophy-room"), bgcolor=theme.text_muted, color="#FFFFFF"),
        ],
        companion=companion.control,
    )

    xp_hud = _build_xp_hud(page, state)
    mission_card = _build_mission_card(page, state, current_lesson, already_completed, summary)
    quiz_card = _build_quiz_card(page, state)
    missions = _build_missions_sidebar(page, state)
    footer = ft.Container(content=ft.Text("More lessons are on their way! 🚀", size=fs(13), color=theme.text_muted))

    sections: list[ft.Control] = [xp_hud, mission_card, quiz_card, missions, footer]
    for section in sections:
        motion.prepare_entrance(section)

    controls: list[ft.Control] = [header]
    for section in sections:
        controls.append(spacer(12))
        controls.append(section)

    view = scene_view("/dashboard", theme, controls)
    motion.play_entrance(page, sections)
    return view


def _build_xp_hud(page: ft.Page, state: AppState) -> ft.Control:
    """Player-level HUD -- the XP-derived player level (see
    ProgressStore.get_player_level), distinct from a lesson's own `level`
    number, two pre-existing meanings of "level" in this app kept visually
    apart here."""
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    player = state.progress.get_player_level()
    ratio = player.xp_into_level / player.xp_needed_for_level if player.xp_needed_for_level else 0.0

    bar = power_bar(theme, ratio, color=theme.success, width=240, height=18)
    play_power_bar(page, bar)

    card = plain_card(
        theme,
        [
            ft.Row(
                [
                    emoji_badge("🏅", size=56, bgcolor=theme.warning, scale=state.font_scale),
                    ft.Column(
                        [
                            ft.Text(f"Player Level {player.level}", size=fs(16), weight=ft.FontWeight.BOLD, color=theme.text),
                            bar,
                            ft.Text(
                                f"{player.xp_into_level}/{player.xp_needed_for_level} XP to Level {player.level + 1}",
                                size=fs(12), color=theme.text_muted,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        data={"kind": "xp_hud", "level": player.level},
    )
    return card


def _build_mission_card(page: ft.Page, state: AppState, current_lesson, already_completed: bool, summary) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    engine = state.lesson_engine
    accent = theme.primary
    text_color = contrasting_text_color(accent)
    meta = get_category_meta(current_lesson.category)

    total_lessons = max(len(engine.main_path_lessons()), 1)
    mission_ratio = min(summary.lessons_completed / total_lessons, 1.0)
    mission_bar = power_bar(theme, mission_ratio, color=theme.star, width=260, height=14)
    play_power_bar(page, mission_bar)

    button_text = "▶ REPLAY" if already_completed else "▶ CONTINUE"
    play_button = build_game_button(
        button_text, lambda _e: page.go(f"/lesson/{current_lesson.id}"), page,
        bgcolor=theme.success, width=280, height=64, size=18, chunky=True,
    )
    motion.pulse(page, play_button.content, times=3, big=1.04)

    return hero_card(
        theme, accent=accent,
        children=[
            ft.Row(
                [
                    emoji_badge(meta.icon, size=56, bgcolor=lighten(meta.color, 0.2), scale=state.font_scale),
                    ft.Column(
                        [
                            ft.Text(f"{meta.title} — Level {current_lesson.category_level}", size=fs(12), color=text_color),
                            ft.Text(current_lesson.title, size=fs(24), weight=ft.FontWeight.BOLD, color=text_color),
                        ],
                        spacing=2, expand=True,
                    ),
                ],
                spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(
                "✅ Completed — replay anytime!" if already_completed else current_lesson.objective,
                size=fs(14), color=text_color,
            ),
            ft.Text(f"Mission progress · {summary.lessons_completed}/{total_lessons}", size=fs(12), color=text_color),
            mission_bar,
            ft.Row([play_button], alignment=ft.MainAxisAlignment.CENTER),
        ],
        padding=22,
        data={"kind": "mission_card", "lesson_id": current_lesson.id, "already_completed": already_completed},
    )


def _build_quiz_card(page: ft.Page, state: AppState) -> ft.Control:
    """Same tile pattern as the Quiz entry in the category browser
    (category_map_flet.py's _build_quiz_tile) -- a quick-access shortcut
    to the same standalone quiz, not a lesson category."""
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    meta = get_category_meta("quiz")
    best = state.progress.get_best_quiz_score()
    status = f"🏆 Best: {best[0]}/{best[1]}" if best else f"{len(state.quiz_engine)} questions · Tap to play!"
    text_color = contrasting_text_color(meta.color)

    return hero_card(
        theme, accent=meta.color,
        children=[
            ft.Row(
                [
                    emoji_badge(meta.icon, size=48, bgcolor=lighten(meta.color, 0.3), scale=state.font_scale),
                    ft.Column(
                        [
                            ft.Text("Quick Quiz", size=fs(17), weight=ft.FontWeight.BOLD, color=text_color),
                            ft.Text(status, size=fs(12), color=text_color),
                        ],
                        spacing=2, expand=True,
                    ),
                ],
                spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        on_click=lambda _e: page.go("/quiz"), padding=16,
        data={"kind": "quiz_card", "status": status},
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
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"{meta.icon} {meta.title}", size=fs(13), weight=ft.FontWeight.BOLD, color=text_color),
                            ft.Text(status, size=fs(12), color=text_color),
                        ],
                        spacing=2,
                    ),
                    bgcolor=meta.color, border_radius=RADIUS_PILL,
                    padding=ft.padding.Padding.symmetric(horizontal=14, vertical=10),
                    on_click=lambda _e, cat=category: page.go(f"/categories/{cat}"), ink=True,
                    data={"kind": "category_chip", "category": category, "status": status},
                )
            )
        items.append(ft.Row(chips, wrap=True, spacing=8, run_spacing=8))

    return plain_card(theme, items, data={"kind": "missions_sidebar", "started": len(started_categories)})
