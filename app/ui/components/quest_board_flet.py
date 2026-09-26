"""Today's Quests board on the Learning Hub: three small daily goals whose
progress is derived from the day's activity (app/engine/quests.py), and a
chunky "Claim bonus" button once all three are done. Rules and the
once-a-day claim live in the engine/store; this component renders. Flet
only.
"""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.engine.quests import QUEST_BONUS_XP, all_quests_done, daily_quests, quest_progress
from app.progress.store import PlayerLevel, today_iso
from app.ui.app_state_flet import AppState
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import RADIUS_PILL, plain_card, soft_shadow
from app.ui.components.game_button_flet import build_game_button
from app.ui.theme_flet import scaled

CLAIMED_TEXT = "✅ Bonus claimed — new quests tomorrow!"


def build_quest_board(
    page, state: AppState, *, scale: float,
    on_bonus_claimed: Optional[Callable[[PlayerLevel], None]] = None,
) -> ft.Container:
    theme = state.theme
    fs = lambda base: scaled(base, scale)  # noqa: E731
    progress = state.progress

    quests = daily_quests(today_iso())
    statuses = quest_progress(quests, progress.get_todays_activity())
    done_count = sum(1 for status in statuses if status.done)
    everything_done = all_quests_done(statuses)
    claimable = everything_done and progress.can_claim_quest_bonus()
    claimed = everything_done and not progress.can_claim_quest_bonus()

    rows: list[ft.Control] = []
    for status in statuses:
        quest = status.quest
        check = "✅" if status.done else f"{status.shown_progress}/{quest.target}"
        title_color = theme.text_muted if status.done else theme.text
        rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(quest.icon, size=fs(20)),
                        ft.Text(quest.title, size=fs(14), weight=ft.FontWeight.BOLD, color=title_color, expand=True),
                        ft.Container(
                            content=ft.Text(check, size=fs(12), weight=ft.FontWeight.BOLD, color=theme.text),
                            bgcolor=theme.bg, border_radius=RADIUS_PILL,
                            padding=ft.padding.Padding.symmetric(horizontal=10, vertical=4),
                        ),
                    ],
                    spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                data={
                    "kind": "quest_row", "quest_id": quest.id, "progress": status.progress,
                    "target": quest.target, "done": status.done,
                },
            )
        )

    footer_text = ft.Text("", size=fs(13), color=theme.text_muted)
    footer_slot = ft.Container(content=footer_text, data={"kind": "quest_footer"})

    board = plain_card(
        theme,
        [
            ft.Row(
                [
                    ft.Text("🗺️ Today's Quests", size=fs(18), weight=ft.FontWeight.BOLD, color=theme.text, expand=True),
                    ft.Text(f"{done_count}/{len(statuses)}", size=fs(14), weight=ft.FontWeight.BOLD, color=theme.primary),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            *rows,
            footer_slot,
        ],
        data={
            "kind": "quest_board", "done": done_count, "total": len(statuses),
            "claimable": claimable, "claimed": claimed,
        },
    )

    def claim(_e) -> None:
        level = progress.claim_quest_bonus(QUEST_BONUS_XP)
        footer_text.value = CLAIMED_TEXT if level is not None else CLAIMED_TEXT
        footer_slot.content = footer_text
        board.data = {**board.data, "claimable": False, "claimed": True}
        page.update()
        motion.pulse(page, board, times=1, big=1.03)
        if level is not None and on_bonus_claimed is not None:
            on_bonus_claimed(level)

    if claimable:
        claim_button = build_game_button(
            f"🏆 Claim +{QUEST_BONUS_XP} XP", claim, page,
            bgcolor=theme.success, height=56, size=16, chunky=True,
        )
        footer_slot.content = ft.Row([claim_button], alignment=ft.MainAxisAlignment.CENTER)
        motion.prepare_pulse(board)
        motion.pulse(page, claim_button.content, times=3, big=1.05)
    elif claimed:
        footer_text.value = CLAIMED_TEXT
    else:
        footer_text.value = f"Finish all {len(statuses)} for a +{QUEST_BONUS_XP} XP bonus!"

    board.shadow = soft_shadow(theme.primary if claimable else "#000000", opacity=0.25 if claimable else 0.12)
    return board
