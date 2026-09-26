"""Codey's Closet (/closet): spend stars on cosmetic outfits for Codey and
choose what he wears. Ownership, balance and the equipped outfit live in
ProgressStore; the catalogue in app/engine/outfits.py. Actions rebuild the
view in place (the same pattern the Settings theme picker uses, since
page.go() to the current route is a no-op in Flet). Flet only.
"""
from __future__ import annotations

import flet as ft

from app.engine.outfits import OUTFITS, Outfit, codey_accessory
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, lighten
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    emoji_badge, hero_card, hero_header, pill_button, plain_card, scene_view, spacer, stat_chip,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.theme_flet import scaled

TILE_WIDTH = 168


def closet_line(balance: int, owned: int, total: int) -> str:
    if owned == total:
        return "You own every outfit! Codey has never looked better ✨"
    if balance == 0:
        return "Earn stars in lessons, then come dress me up! ⭐"
    return f"Ooh, {balance} stars to spend! What should I wear today?"


def build_closet_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    progress = state.progress
    balance = progress.get_star_balance()
    owned = set(progress.get_owned_outfits())
    equipped = progress.get_equipped_outfit()
    level = progress.get_player_level().level

    companion = build_codey_companion(
        theme, scale, closet_line(balance, len(owned), len(OUTFITS)), page=page,
        accessory=codey_accessory(equipped, level),
    )
    header = hero_header(
        theme, title="👕 Codey's Closet", scale=scale,
        buttons=[pill_button("🏠 Menu", lambda _e: page.go("/hub"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
    )

    balance_row = ft.Row(
        [
            stat_chip(theme, "⭐", f"{balance} stars to spend", scale, kind="star_balance"),
            stat_chip(theme, "👕", f"{len(owned)}/{len(OUTFITS)} owned", scale, kind="owned_count"),
        ],
        wrap=True, spacing=8, run_spacing=8,
    )

    def rebuild() -> None:
        views = getattr(page, "views", None)
        if views is not None:
            views.clear()
            views.append(build_closet_view(page, state))
        page.update()

    tiles: list[ft.Control] = [_build_none_tile(page, state, equipped, rebuild)]
    for outfit in OUTFITS:
        tiles.append(_build_outfit_tile(page, state, outfit, balance, outfit.id in owned, outfit.id == equipped, rebuild))
    grid = ft.Row(tiles, wrap=True, spacing=12, run_spacing=12)

    sections: list[ft.Control] = [balance_row, plain_card(theme, [grid], padding=14, data={"kind": "closet_grid"})]
    for section in sections:
        motion.prepare_entrance(section)
    controls: list[ft.Control] = [header]
    for section in sections:
        controls.append(spacer(12))
        controls.append(section)
    view = scene_view("/closet", theme, controls, page=page)
    motion.play_entrance(page, sections)
    return view


def _build_none_tile(page, state: AppState, equipped, rebuild) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    is_equipped = equipped is None

    def take_off(_e=None) -> None:
        state.progress.equip_outfit(None)
        rebuild()

    return hero_card(
        theme, accent=theme.text_muted, width=TILE_WIDTH, padding=14,
        children=[
            ft.Row([emoji_badge("🤖", size=56, bgcolor=lighten(theme.text_muted, 0.3), scale=state.font_scale)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("Just Codey", size=fs(14), weight=ft.FontWeight.BOLD, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
            ft.Text("Wears the badge for your level", size=fs(11), color="#FFFFFF", text_align=ft.TextAlign.CENTER),
            ft.Button(
                "Wearing ✓" if is_equipped else "Wear", on_click=None if is_equipped else take_off,
                disabled=is_equipped, height=40, style=ft.ButtonStyle(bgcolor=theme.card, color=theme.text),
            ),
        ],
        data={"kind": "outfit_tile", "id": None, "owned": True, "equipped": is_equipped, "affordable": True},
    )


def _build_outfit_tile(page, state: AppState, outfit: Outfit, balance: int, owned: bool, is_equipped: bool, rebuild) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    affordable = balance >= outfit.price
    accent = theme.star if owned else (theme.primary if affordable else theme.text_muted)
    text_color = contrasting_text_color(accent)

    def buy(_e=None) -> None:
        if state.progress.buy_outfit(outfit.id, outfit.price):
            rebuild()

    def wear(_e=None) -> None:
        state.progress.equip_outfit(outfit.id)
        rebuild()

    if is_equipped:
        button = ft.Button("Wearing ✓", disabled=True, height=40, style=ft.ButtonStyle(bgcolor=theme.card, color=theme.text))
        status = "Looking sharp!"
    elif owned:
        button = ft.Button("Wear", on_click=wear, height=40, style=ft.ButtonStyle(bgcolor=theme.card, color=theme.text))
        status = "Owned"
    elif affordable:
        button = ft.Button(f"Buy ⭐{outfit.price}", on_click=buy, height=40, style=ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF"))
        status = f"⭐ {outfit.price} stars"
    else:
        button = ft.Button(f"Need ⭐{outfit.price - balance} more", disabled=True, height=40, style=ft.ButtonStyle(bgcolor=theme.card, color=theme.text_muted))
        status = f"⭐ {outfit.price} stars"

    disc = emoji_badge(outfit.emoji, size=56, bgcolor=lighten(accent, 0.35), scale=state.font_scale, lip=owned or affordable)
    if is_equipped:
        motion.prepare_pulse(disc)
        motion.pulse(page, disc, times=2, big=1.1)

    return hero_card(
        theme, accent=accent, width=TILE_WIDTH, padding=14,
        children=[
            ft.Row([disc], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text(outfit.title, size=fs(14), weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER),
            ft.Text(status, size=fs(11), color=text_color, text_align=ft.TextAlign.CENTER),
            button,
        ],
        data={"kind": "outfit_tile", "id": outfit.id, "owned": owned, "equipped": is_equipped, "affordable": affordable},
    )
