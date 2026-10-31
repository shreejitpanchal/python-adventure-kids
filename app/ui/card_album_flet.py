"""The Card Album (/cards): every concept card the curriculum can produce,
collected ones face up with their level pips, the rest face down. Rules in
app/engine/cards.py (cards are derived from completed lessons' tags, so
there is nothing to store); this screen only draws. Tapping a collected
card wobbles it and shows its blurb. Flet only.
"""
from __future__ import annotations

import flet as ft

from app.engine.cards import ConceptCard, album_line, all_cards
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    accent_gradient, hero_header, lip_shadow, pill_button, plain_card, play_power_bar, power_bar, pressable,
    scene_view, soft_shadow, spacer,
)
from app.ui.components.ambience_flet import build_sky_backdrop, sky_moment
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.nav_bar_flet import build_nav_bar
from app.ui.theme_flet import scaled

CARD_WIDTH = 150
RARITY_LABELS = {"common": "Common", "rare": "Rare ✦", "legendary": "Legendary ★"}


def codey_album_line(collected: int, total: int) -> str:
    return album_line(collected, total) or "No cards in this curriculum yet."


def build_card_album_view(page: ft.Page, state: AppState, *, hour: int | None = None) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    fs = lambda base: scaled(base, scale)  # noqa: E731
    cards = all_cards(state.lesson_engine, state.progress.get_completed_lesson_ids())
    collected = [card for card in cards if card.collected]

    companion = build_codey_companion(theme, scale, codey_album_line(len(collected), len(cards)), page=page)
    header = hero_header(
        theme, title="🃏 Card Album", scale=scale,
        buttons=[pill_button("🏆 Trophy Room", lambda _e: page.go("/trophy-room"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
        backdrop=build_sky_backdrop(theme, moment=sky_moment(hour), scale=scale, page=page),
    )

    ratio = len(collected) / len(cards) if cards else 0.0
    bar = power_bar(theme, ratio, color=theme.star, width=260, height=14)
    play_power_bar(page, bar)
    progress_card = plain_card(
        theme,
        [ft.Text(f"{len(collected)}/{len(cards)} cards collected", size=fs(14), weight=ft.FontWeight.BOLD, color=theme.text), bar],
        data={"kind": "album_progress", "collected": len(collected), "total": len(cards)},
    )

    tiles = [_build_card_tile(page, state, card, scale) for card in cards]
    shelf = ft.Row(tiles, wrap=True, spacing=14, run_spacing=14, alignment=ft.MainAxisAlignment.CENTER, data={"kind": "album_shelf"})

    sections = [progress_card, shelf]
    for section in sections:
        motion.prepare_entrance(section)
    view = scene_view(
        "/cards", theme, [header, spacer(12), progress_card, spacer(12), shelf], page=page,
        nav_bar=build_nav_bar(page, theme, "trophies", scale=scale, state=state),
    )
    motion.play_entrance(page, sections)
    return view


def _build_card_tile(page: ft.Page, state: AppState, card: ConceptCard, scale: float) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = card.meta
    accent = meta.color if card.collected else theme.text_muted
    text_color = contrasting_text_color(accent) if card.collected else theme.text_muted
    pips = "●" * min(card.level, 5) + "○" * max(0, min(card.total, 5) - min(card.level, 5))

    icon = ft.Text(meta.icon if card.collected else "🂠", size=fs(40), text_align=ft.TextAlign.CENTER)
    title = ft.Text(meta.title if card.collected else "???", size=fs(14), weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER)
    rarity = ft.Text(RARITY_LABELS[card.rarity], size=fs(10), color=text_color, text_align=ft.TextAlign.CENTER)
    level = ft.Text(f"Lv {card.level}  {pips}" if card.collected else "Finish a lesson to flip", size=fs(11), color=text_color, text_align=ft.TextAlign.CENTER)
    blurb = ft.Text(meta.blurb, size=fs(11), italic=True, color=text_color, text_align=ft.TextAlign.CENTER, visible=False)

    # A card frame: a lighter inner panel inside the colored border, with a
    # shimmer rim for rare and legendary cards.
    rim = {"common": None, "rare": ft.border.Border.all(3, with_alpha("#FFFFFF", 0.7)), "legendary": ft.border.Border.all(3, theme.star)}[card.rarity]
    tile = ft.Container(
        content=ft.Container(
            content=ft.Column([icon, title, rarity, level, blurb], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=with_alpha(lighten(accent, 0.6), 0.35) if card.collected else None,
            border_radius=14, padding=10,
        ),
        width=CARD_WIDTH, padding=6, border_radius=18,
        gradient=accent_gradient(accent) if card.collected else None,
        bgcolor=None if card.collected else with_alpha(theme.text_muted, 0.15),
        shadow=[lip_shadow(accent, depth=5), soft_shadow(accent, opacity=0.25)] if card.collected else None,
        border=rim if card.collected else None,
        rotate=0.0, animate_rotation=ft.Animation(90, ft.AnimationCurve.EASE_IN_OUT),
        data={"kind": "concept_card", "tag": card.tag, "collected": card.collected, "level": card.level, "rarity": card.rarity},
    )

    if card.collected:
        def toggle(_e: ft.ControlEvent) -> None:
            blurb.visible = not blurb.visible
            page.update()
            motion.wobble(page, tile, times=4, angle=0.06)

        tile.on_click = toggle
        tile.ink = True
        pressable(tile, page, state=state)
    return tile
