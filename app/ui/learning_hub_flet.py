"""Learning Hub: the top-of-hierarchy screen for the Flet app, styled as
the game world's base camp -- a sky hero header with Codey greeting the
child, a HUD strip (streak flame, level + title, stars, badges), the Daily
Treasure chest, Today's Quests, the once-a-day welcome-back moment, and
six colorful "world tiles" (guided path, two Code Cracker tracks,
projects, and the Python Learning and AI & Machine Learning courses)
instead of dropping straight into "Today's Mission" the way the old
dashboard did. All status text is computed once in
app/engine/hub_status.py and just rendered here; this screen never
recomputes progress numbers itself.

Settings and Parent Area live in this screen's header, not the Dashboard's
-- this is the true top of the navigation hierarchy, so they only need one
home.

Visuals come from app/ui/components/adventure_kit_flet.py; the retention
pieces from streak_flame_flet.py / treasure_chest_flet.py /
quest_board_flet.py / codey_avatar_flet.py. Key controls carry
data={"kind": ...} for tests. In a wide window (layout_for) the tiles
form a wrapping two-up grid instead of a single column.
"""
from __future__ import annotations

import flet as ft

from app.engine.hub_status import compute_hub_status
from app.engine.league import MEDALS, child_rank, league_line, league_standings, weekly_xp_from_events
from app.engine.outfits import codey_accessory
from app.engine.quests import all_quests_done, daily_quests, quest_progress
from app.engine.titles import level_title
from app.progress.store import today_iso, week_key
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    RADIUS_PILL, emoji_badge, hero_card, hero_header, layout_for, pill_button, scene_view, section_title, spacer,
    stat_chip,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.quest_board_flet import build_quest_board
from app.ui.components.streak_flame_flet import (
    build_shield_chip, build_streak_chip, build_welcome_banner, welcome_message,
)
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
# an older settings.json carries one) map onto the Hub's own card keys,
# which mirror last_learning_route's vocabulary instead (guided/
# code_crackers/advanced_code_crackers/projects) -- "crackers" means the
# (non-advanced) Code Crackers card.
_PREFERRED_MODE_TO_CARD_KEY: dict[str, str] = {
    "guided": "guided",
    "projects": "projects",
    "crackers": "code_crackers",
    "advanced": "advanced_code_crackers",
}


def codey_hub_line(
    name: str, streak_days: int, has_resume: bool, chest_available: bool, quests_ready: bool = False,
) -> str:
    """What Codey says in the Hub header -- the most actionable nudge wins:
    a claimable quest bonus, an unopened chest, then an unfinished route,
    then streak pride."""
    if quests_ready:
        return "All of today's quests are done — claim your bonus! 🏆"
    if chest_available and streak_days >= 3:
        return f"{streak_days} days in a row, {name}! Grab your treasure, then let's play! 🔥"
    if chest_available:
        return "A treasure chest is waiting for you today! 🎁"
    if has_resume:
        return "Want to pick up where you left off?"
    if streak_days >= 3:
        return f"{streak_days} days in a row! Let's keep the fire going 🔥"
    return f"Ready for today's adventure, {name}? Let's go!"


def level_chip_label(level: int) -> str:
    return f"Lv {level} · {level_title(level).title}"


def build_learning_hub_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    layout = layout_for(page)
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)
    summary = state.progress.get_summary()
    player = state.progress.get_player_level()
    name = state.settings.child_name or "Explorer"

    # The welcome-back moment plays once per launch-day: consume it here so
    # navigating back to the Hub later doesn't replay it.
    message = welcome_message(name, state.welcome)
    state.welcome = None

    chest_available = state.progress.can_open_daily_chest()
    quest_statuses = quest_progress(daily_quests(today_iso()), state.progress.get_todays_activity())
    quests_ready = all_quests_done(quest_statuses) and state.progress.can_claim_quest_bonus()
    companion = build_codey_companion(
        theme, scale,
        codey_hub_line(name, summary.streak_days, hub_status.resume_label is not None, chest_available, quests_ready),
        page=page, accessory=codey_accessory(state.progress.get_equipped_outfit(), player.level),
    )
    header = hero_header(
        theme, title="Python Adventure", scale=scale,
        buttons=[
            pill_button("👕 Closet", lambda _e: page.go("/closet"), bgcolor=theme.primary),
            pill_button("🏆 Trophies", lambda _e: page.go("/trophy-room"), bgcolor=theme.text_muted, color="#FFFFFF"),
            pill_button("⚙️ Settings", lambda _e: page.go("/settings"), bgcolor=theme.text_muted, color="#FFFFFF"),
            pill_button("👋 Parent Area", lambda _e: page.go("/parent"), bgcolor=theme.text_muted, color="#FFFFFF"),
        ],
        companion=companion.control,
    )

    level_chip = stat_chip(theme, "🏅", level_chip_label(player.level), scale, kind="level_chip")
    xp_chip = stat_chip(theme, "⚡", f"{player.xp_into_level}/{player.xp_needed_for_level} XP", scale, kind="xp_chip")
    chips: list[ft.Control] = [build_streak_chip(theme, summary.streak_days, scale, page=page)]
    if summary.streak_shields > 0:
        chips.append(build_shield_chip(theme, summary.streak_shields, scale))
    chips.extend([
        level_chip,
        xp_chip,
        stat_chip(theme, "⭐", f"{summary.total_stars} stars", scale),
        stat_chip(theme, "🎖️", f"{summary.badges_earned} badges", scale),
    ])
    stats = ft.Row(chips, wrap=True, spacing=8, run_spacing=8, data={"kind": "hud_strip"})

    def refresh_hud(level) -> None:
        level_chip.content.controls[1].value = level_chip_label(level.level)
        xp_chip.content.controls[1].value = f"{level.xp_into_level}/{level.xp_needed_for_level} XP"

    def on_chest_opened(reward) -> None:
        refresh_hud(reward.level)
        companion.set_line("Ooh, treasure! Now let's earn some stars ⭐")
        companion.cheer(page)
        page.update()

    def on_bonus_claimed(level) -> None:
        refresh_hud(level)
        companion.set_line("Quest bonus collected — you're unstoppable! 🏆")
        companion.cheer(page)
        page.update()

    chest = build_daily_chest(page, state, scale=scale, on_opened=on_chest_opened)
    quest_board = build_quest_board(page, state, scale=scale, on_bonus_claimed=on_bonus_claimed)

    sections: list[ft.Control] = []
    if message is not None:
        sections.append(build_welcome_banner(theme, message, scale, page=page))
    sections.append(stats)
    sections.append(chest)
    sections.append(quest_board)
    if state.settings.league_enabled:
        sections.append(_build_league_card(state, name))
    if hub_status.resume_label is not None:
        sections.append(_build_resume_banner(page, state, hub_status.resume_label))
    sections.append(ft.Container(content=section_title(theme, "🗺️ Choose your adventure", scale)))

    cards = _build_cards(page, state, hub_status, layout.card_width)
    if layout.wide:
        sections.append(ft.Row(cards, wrap=True, spacing=12, run_spacing=12, data={"kind": "card_grid"}))
    else:
        sections.extend(cards)

    for section in sections:
        motion.prepare_entrance(section)

    controls: list[ft.Control] = [header]
    for section in sections:
        controls.append(spacer(12))
        controls.append(section)

    view = scene_view("/hub", theme, controls, page=page)
    motion.play_entrance(page, sections)
    return view


def _build_league_card(state: AppState, name: str) -> ft.Control:
    """This week's league table (app/engine/league.py): Codey's friends'
    generated scores around the child's real weekly XP, the child's row
    highlighted, and a nudge line underneath."""
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    child_xp = weekly_xp_from_events(state.progress.get_week_activity())
    standings = league_standings(name, child_xp, week_key())
    rank = child_rank(standings)

    rows: list[ft.Control] = []
    for index, standing in enumerate(standings):
        medal = MEDALS[index] if index < len(MEDALS) else f"{index + 1}."
        row_color = theme.primary if standing.is_child else theme.card
        row_text = contrasting_text_color(row_color) if standing.is_child else theme.text
        rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(medal, size=fs(16), width=32),
                        ft.Text(standing.emoji, size=fs(18)),
                        ft.Text(f"{standing.name}{' (you)' if standing.is_child else ''}", size=fs(14), weight=ft.FontWeight.BOLD, color=row_text, expand=True),
                        ft.Text(f"{standing.xp} XP", size=fs(13), weight=ft.FontWeight.BOLD, color=row_text),
                    ],
                    spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=row_color if standing.is_child else None,
                border_radius=12, padding=ft.padding.Padding.symmetric(horizontal=10, vertical=6),
                data={"kind": "league_row", "name": standing.name, "xp": standing.xp, "is_child": standing.is_child},
            )
        )

    return plain_card(
        theme,
        [
            ft.Row(
                [
                    ft.Text("🏁 Weekly League", size=fs(18), weight=ft.FontWeight.BOLD, color=theme.text, expand=True),
                    ft.Text(f"You're #{rank}", size=fs(14), weight=ft.FontWeight.BOLD, color=theme.primary),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            *rows,
            ft.Text(league_line(standings), size=fs(13), italic=True, color=theme.text_muted),
        ],
        spacing=6,
        data={"kind": "league_card", "rank": rank, "child_xp": child_xp},
    )


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


def _build_cards(page: ft.Page, state: AppState, hub_status, card_width: int | None) -> list[ft.Control]:
    preferred = _PREFERRED_MODE_TO_CARD_KEY.get(state.settings.preferred_learning_mode, "guided")

    ordered_defs = sorted(
        _CARD_DEFS, key=lambda card_def: 0 if card_def[0] == preferred else 1,
    )

    return [
        _build_card(
            page, state, key, icon, title, subtitle, getattr(hub_status, status_attr), route,
            key == preferred, card_width,
        )
        for key, icon, title, subtitle, status_attr, route in ordered_defs
    ]


def _build_card(
    page: ft.Page, state: AppState, key: str, icon: str, title: str, subtitle: str,
    status: str, route: str, featured: bool, card_width: int | None,
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
        padding=22 if featured else 16, width=card_width,
        data={"kind": "hub_card", "key": key, "title": title, "status": status, "route": route, "featured": featured},
    )
