"""Trophy Room: a shelf of badges. Earned ones show their icon and title on
a gold, chunky tile; tapping one gives a little tactile wobble and reveals
when it was earned and what it's for. Not-yet-earned badges show as grayed
"???" placeholders (from the same curated registry, app/engine/badges.py,
which now includes one champion badge per map World), encouraging
"collect them all" without spoiling what they are.

Flet only, per the CTk-parity decisions made for phases 7-9.
"""
from __future__ import annotations

from datetime import datetime

import flet as ft

from app.engine.badges import BADGE_META, get_badge_meta
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import (
    accent_gradient, hero_header, lip_shadow, pill_button, plain_card, play_power_bar, power_bar, scene_view, spacer,
)
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.theme_flet import scaled


def _format_earned_date(iso_timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return iso_timestamp
    return dt.strftime("%B %d, %Y")


def codey_trophy_line(earned: int, total: int) -> str:
    if total and earned == total:
        return "You collected every badge! Absolute legend 🏆"
    if earned == 0:
        return "Your shelf is waiting. Finish a lesson to earn your first badge!"
    return f"{earned} of {total} badges collected — keep going!"


def build_trophy_room_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    scale = state.font_scale
    fs = lambda base: scaled(base, scale)  # noqa: E731

    earned_by_id = dict(state.progress.get_badges_with_dates())
    all_badge_ids = list(BADGE_META.keys())
    # An earned badge outside the curated registry (falls back to
    # DEFAULT_BADGE_META) still gets a card -- nothing earned is ever hidden.
    for badge_id in earned_by_id:
        if badge_id not in all_badge_ids:
            all_badge_ids.append(badge_id)

    companion = build_codey_companion(theme, scale, codey_trophy_line(len(earned_by_id), len(all_badge_ids)), page=page)
    header = hero_header(
        theme, title="🏆 Trophy Room", scale=scale,
        buttons=[pill_button("🏠 Menu", lambda _e: page.go("/hub"), bgcolor=theme.text_muted, color="#FFFFFF")],
        companion=companion.control,
    )

    progress_text = ft.Text(
        f"{len(earned_by_id)}/{len(all_badge_ids)} badges collected", size=fs(14), weight=ft.FontWeight.BOLD, color=theme.text,
    )
    ratio = len(earned_by_id) / len(all_badge_ids) if all_badge_ids else 0.0
    bar = power_bar(theme, ratio, color=theme.star, width=260, height=14)
    play_power_bar(page, bar)
    progress_card = plain_card(theme, [bar], data={"kind": "trophy_progress", "earned": len(earned_by_id)})

    cards = [
        _build_badge_card(page, theme, badge_id, earned_by_id.get(badge_id), scale)
        for badge_id in all_badge_ids
    ]
    shelf = ft.Row(cards, wrap=True, spacing=16, run_spacing=16, alignment=ft.MainAxisAlignment.CENTER)

    for section in (progress_card, shelf):
        motion.prepare_entrance(section)
    view = scene_view("/trophy-room", theme, [header, progress_text, progress_card, spacer(4), shelf], page=page)
    motion.play_entrance(page, [progress_card, shelf])
    return view


def _build_badge_card(page: ft.Page, theme, badge_id: str, earned_at: str | None, scale: float) -> ft.Control:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = get_badge_meta(badge_id)
    is_earned = earned_at is not None
    text_color = contrasting_text_color(theme.star) if is_earned else theme.text_muted

    icon_text = ft.Text(meta.icon if is_earned else "🔒", size=fs(40), text_align=ft.TextAlign.CENTER)
    title_text = ft.Text(
        meta.title if is_earned else "???", size=fs(14), weight=ft.FontWeight.BOLD,
        color=text_color, text_align=ft.TextAlign.CENTER,
    )
    detail_text = ft.Text("", size=fs(11), color=text_color, text_align=ft.TextAlign.CENTER, visible=False)

    card = ft.Container(
        content=ft.Column(
            [icon_text, title_text, detail_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
        ),
        gradient=accent_gradient(theme.star) if is_earned else None,
        bgcolor=None if is_earned else with_alpha(theme.text_muted, 0.15),
        shadow=lip_shadow(theme.star, depth=5) if is_earned else None,
        border_radius=20, padding=16, width=150,
        rotate=0.0, animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        data={"kind": "badge_card", "badge_id": badge_id, "earned": is_earned},
    )

    if is_earned:
        def toggle(_e: ft.ControlEvent) -> None:
            detail_text.visible = not detail_text.visible
            if detail_text.visible:
                detail_text.value = f"{meta.description}\nEarned {_format_earned_date(earned_at)}"
                card.rotate = 0.05
            else:
                card.rotate = 0.0
            page.update()

        card.on_click = toggle
        card.ink = True

    return card
