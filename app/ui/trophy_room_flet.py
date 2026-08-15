"""Trophy Room: a shelf of badges. Earned ones show their icon and title;
tapping one gives a little tactile wobble and reveals when it was earned
and what it's for. Not-yet-earned badges show as grayed "???" placeholders
(from the same curated registry, app/engine/badges.py), encouraging
"collect them all" without spoiling what they are.

Flet only, per the CTk-parity decisions made for phases 7-9. No chime
sound (per the spec's "tap plays a chime" idea) -- this app has no audio
playback infrastructure anywhere yet (Settings.sound_enabled is a stored
preference with nothing behind it), and adding one is bigger than this
phase's scope.
"""
from __future__ import annotations

from datetime import datetime

import flet as ft

from app.engine.badges import BADGE_META, get_badge_meta
from app.ui.app_state_flet import AppState


def _format_earned_date(iso_timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return iso_timestamp
    return dt.strftime("%B %d, %Y")


def build_trophy_room_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text("🏆 Trophy Room", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )

    earned_by_id = dict(state.progress.get_badges_with_dates())
    all_badge_ids = list(BADGE_META.keys())
    # An earned badge outside the curated registry (falls back to
    # DEFAULT_BADGE_META) still gets a card -- nothing earned is ever hidden.
    for badge_id in earned_by_id:
        if badge_id not in all_badge_ids:
            all_badge_ids.append(badge_id)

    cards = [
        _build_badge_card(page, theme, badge_id, earned_by_id.get(badge_id))
        for badge_id in all_badge_ids
    ]

    progress_text = ft.Text(
        f"{len(earned_by_id)}/{len(all_badge_ids)} badges collected", size=14, color=theme.text_muted,
    )

    return ft.View(
        route="/trophy-room",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[
            header,
            progress_text,
            ft.Row(cards, wrap=True, spacing=16, run_spacing=16),
        ],
    )


def _build_badge_card(page: ft.Page, theme, badge_id: str, earned_at: str | None) -> ft.Control:
    meta = get_badge_meta(badge_id)
    is_earned = earned_at is not None

    icon_text = ft.Text(meta.icon if is_earned else "🔒", size=40)
    title_text = ft.Text(
        meta.title if is_earned else "???", size=14, weight=ft.FontWeight.BOLD,
        color=theme.text if is_earned else theme.text_muted, text_align=ft.TextAlign.CENTER,
    )
    detail_text = ft.Text("", size=11, color=theme.text_muted, text_align=ft.TextAlign.CENTER, visible=False)

    card = ft.Container(
        content=ft.Column(
            [icon_text, title_text, detail_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
        ),
        bgcolor=theme.card if is_earned else theme.bg,
        border_radius=16, padding=16, width=140,
        rotate=0.0, animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
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
