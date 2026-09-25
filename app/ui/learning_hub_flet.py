"""Learning Hub: the top-of-hierarchy screen for the Flet app, styled as
the game world's base camp -- a sky hero header with Codey greeting the
child, a HUD strip (streak flame, level, stars, badges), the Daily
Treasure chest, the once-a-day welcome-back moment, and six colorful
"world tiles" (guided path, two Code Cracker tracks, projects, and the
Python Learning and AI & Machine Learning courses) instead of dropping
straight into "Today's Mission" the way the old dashboard did. All status
text is computed once in app/engine/hub_status.py and just rendered here;
this screen never recomputes progress numbers itself.

Settings and Parent Area live in this screen's header, not the Dashboard's
-- this is the true top of the navigation hierarchy, so they only need one
home.

Visuals come from app/ui/components/adventure_kit_flet.py; the retention
pieces from streak_flame_flet.py / treasure_chest_flet.py /
codey_avatar_flet.py. Key controls carry data={"kind": ...} for tests.
"""
from __future__ import annotations

import flet as ft

from app.engine.hub_status import compute_hub_status
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    RADIUS_PILL, emoji_badge, hero_card, hero_header, pill_button, scene_view, section_title, spacer,
    stat_chip,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.streak_flame_flet import build_streak_chip, build_welcome_banner, welcome_message
from app.ui.components.treasure_chest_flet import build_daily_chest
from app.ui.theme_flet import scaled

# Card key -> concrete route. Shared by both the resume banner and the
# cards themselves, and matches Settings.last_learning_route's semantic
# values (see app/config/settings.py + app/engine/hub_status.py).
_ROUTES: dict[str, str] = {
    "guided": "/dashboard",
    "code_crackers": "/categories/code_crackers",
    "advanced_code_crackers": "/categories/advanced_code_crackers",
    "projects": "/projects",
    "course": "/course",
    "ai_course": "/ai-course",
}

# Card definitions in fixed relative order. Each entry: (key, icon, title,
# subtitle, hub_status attribute name, route).
_CARD_DEFS: list[tuple[str, str, str, str, str, str]] = [
    (
        "guided", "🚀", "Start Learning Python",
        "A guided path for beginners. Continue your next lesson.",
        "guided_status", "/dashboard",
    ),
    (
        "code_crackers", "🐛", "Fix Code Cracker Puzzles",
        "Find and fix bugs in short Python programs.",
        "cracker_status", "/categories/code_crackers",
    ),
    (
        "advanced_code_crackers", "🧠", "Advanced Code Crackers",
        "Tricky real-world Python bugs for experienced coders.",
        "advanced_cracker_status", "/categories/advanced_code_crackers",
    ),
    (
        "projects", "🛠️", "Build a Project",
        "Games, art, adventures, and coding challenges.",
        "project_status", "/projects",
    ),
    (
        "course", "🎓", "Python Learning",
        "A structured 7-chapter course with lessons, sample programs, and quizzes.",
        "course_status", "/course",
    ),
    (
        "ai_course", "🤖", "AI & Machine Learning",
        "Learn how AI, machine learning, and MCP work -- through hands-on simulations.",
        "ai_course_status", "/ai-course",
    ),
]

# Each world tile's region color. None -> the theme's primary, so the
# guided path always matches the current skin; the rest mirror the
# category colors in app/engine/categories.py where one exists.
_CARD_ACCENTS: dict[str, str | None] = {
    "guided": None,
    "code_crackers": "#D4A017",
    "advanced_code_crackers": "#5C6BC0",
    "projects": "#EF5350",
    "course": "#4F46E5",
    "ai_course": "#7C4DFF",
}

# Settings.preferred_learning_mode's semantic keys (guided/projects/
# crackers/advanced -- no longer asked by the setup wizard, but honored if
# an older settings.json carries one) map onto the Hub's own card keys, which mirror last_learning_route's
# vocabulary instead (guided/code_crackers/advanced_code_crackers/projects)
# -- "crackers" means the (non-advanced) Code Crackers card.
_PREFERRED_MODE_TO_CARD_KEY: dict[str, str] = {
    "guided": "guided",
    "projects": "projects",
    "crackers": "code_crackers",
    "advanced": "advanced_code_crackers",
}


def codey_hub_line(name: str, streak_days: int, has_resume: bool, chest_available: bool) -> str:
    """What Codey says in the Hub header -- the most actionable nudge wins:
    an unopened chest, then an unfinished route, then streak pride."""
    if chest_available and streak_days >= 3:
        return f"{streak_days} days in a row, {name}! Grab your treasure, then let's play! 🔥"
    if chest_available:
        return "A treasure chest is waiting for you today! 🎁"
    if has_resume:
        return "Want to pick up where you left off?"
    if streak_days >= 3:
        return f"{streak_days} days in a row! Let's keep the fire going 🔥"
    return f"Ready for today's adventure, {name}? Let's go!"


def build_learning_hub_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    summary = state.progress.get_summary()
    player = state.progress.get_player_level()
    name = state.settings.child_name or "Explorer"

    # The welcome-back moment plays once per launch-day: consume it here so
    # navigating back to the Hub later doesn't replay it.
    message = welcome_message(name, state.welcome)
    state.welcome = None

    chest_available = state.progress.can_open_daily_chest()
    companion = build_codey_companion(
        theme, scale,
        codey_hub_line(name, summary.streak_days, hub_status.resume_label is not None, chest_available),
        page=page,
    )
    header = hero_header(
        theme, title="Python Adventure", scale=scale,
        buttons=[
            pill_button("⚙️ Settings", lambda _e: page.go("/settings"), bgcolor=theme.text_muted, color="#FFFFFF"),
            pill_button("👋 Parent Area", lambda _e: page.go("/parent"), bgcolor=theme.text_muted, color="#FFFFFF"),
        ],
        companion=companion.control,
    )

    level_chip = stat_chip(theme, "🏅", f"Level {player.level}", scale, kind="level_chip")
    xp_chip = stat_chip(theme, "⚡", f"{player.xp_into_level}/{player.xp_needed_for_level} XP", scale, kind="xp_chip")
    stats = ft.Row(
        [
            build_streak_chip(theme, summary.streak_days, scale, page=page),
            level_chip,
            xp_chip,
            stat_chip(theme, "⭐", f"{summary.total_stars} stars", scale),
            stat_chip(theme, "🎖️", f"{summary.badges_earned} badges", scale),
        ],
        wrap=True, spacing=8, run_spacing=8,
        data={"kind": "hud_strip"},
    )

    def on_chest_opened(reward) -> None:
        level_chip.content.controls[1].value = f"Level {reward.level.level}"
        xp_chip.content.controls[1].value = f"{reward.level.xp_into_level}/{reward.level.xp_needed_for_level} XP"
        companion.set_line("Ooh, treasure! Now let's earn some stars ⭐")
        companion.cheer(page)
        page.update()

    chest = build_daily_chest(page, state, scale=scale, on_opened=on_chest_opened)

    sections: list[ft.Control] = []
    if message is not None:
        sections.append(build_welcome_banner(theme, message, scale, page=page))
    sections.append(stats)
    sections.append(chest)
    if hub_status.resume_label is not None:
        sections.append(_build_resume_banner(page, state, hub_status.resume_label))
    sections.append(ft.Container(content=section_title(theme, "🗺️ Choose your adventure", scale)))
    sections.extend(_build_cards(page, state, hub_status))

    for section in sections:
        motion.prepare_entrance(section)

    controls: list[ft.Control] = [header]
    for section in sections:
        controls.append(spacer(12))
        controls.append(section)

    view = scene_view("/hub", theme, controls)
    motion.play_entrance(page, sections)
    return view


def _build_resume_banner(page: ft.Page, state: AppState, resume_label: str) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    route_key = state.settings.last_learning_route
    target_route = _ROUTES.get(route_key, "/hub")

    def on_click(_e: ft.ControlEvent) -> None:
        page.go(target_route)

    return ft.Container(
        content=ft.Text(
            f"↩ {resume_label}", size=fs(14), weight=ft.FontWeight.BOLD,
            color=contrasting_text_color(theme.primary),
        ),
        bgcolor=theme.primary, border_radius=RADIUS_PILL,
        padding=ft.padding.Padding.symmetric(horizontal=18, vertical=14),
        on_click=on_click, ink=True,
        data={"kind": "resume_banner", "route": target_route, "label": resume_label},
    )


def _build_cards(page: ft.Page, state: AppState, hub_status) -> list[ft.Control]:
    preferred = _PREFERRED_MODE_TO_CARD_KEY.get(state.settings.preferred_learning_mode, "guided")

    ordered_defs = sorted(
        _CARD_DEFS, key=lambda card_def: 0 if card_def[0] == preferred else 1,
    )

    return [
        _build_card(page, state, key, icon, title, subtitle, getattr(hub_status, status_attr), route, key == preferred)
        for key, icon, title, subtitle, status_attr, route in ordered_defs
    ]


def _build_card(
    page: ft.Page, state: AppState, key: str, icon: str, title: str, subtitle: str,
    status: str, route: str, featured: bool,
) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    accent = _CARD_ACCENTS.get(key) or theme.primary
    text_color = contrasting_text_color(accent)

    def on_click(_e: ft.ControlEvent) -> None:
        state.settings.last_learning_route = key
        state.save_settings()
        page.go(route)

    children: list[ft.Control] = [
        ft.Row(
            [
                emoji_badge(icon, size=60 if featured else 48, bgcolor=lighten(accent, 0.35), scale=state.font_scale),
                # expand=True lets the title wrap onto a second line at
                # large font scales instead of overflowing the tile.
                ft.Text(title, size=fs(22) if featured else fs(17), weight=ft.FontWeight.BOLD, color=text_color, expand=True),
            ],
            spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        ft.Text(subtitle, size=fs(14) if featured else fs(13), color=text_color),
        ft.Row(
            [
                ft.Container(
                    content=ft.Text(status, size=fs(12), weight=ft.FontWeight.BOLD, color="#232323"),
                    bgcolor=with_alpha("#FFFFFF", 0.88), border_radius=RADIUS_PILL,
                    padding=ft.padding.Padding.symmetric(horizontal=12, vertical=6),
                ),
            ],
            wrap=True,
        ),
    ]
    if featured:
        children.append(ft.Text("▶ TAP TO PLAY", size=fs(13), weight=ft.FontWeight.BOLD, color=text_color))

    return hero_card(
        theme, accent=accent, children=children, on_click=on_click, featured=featured,
        padding=22 if featured else 16,
        data={"kind": "hub_card", "key": key, "title": title, "status": status, "route": route, "featured": featured},
    )
