"""Codey the Robot -- the app's companion mascot. Two forms:

- build_codey_avatar(): the small in-lesson reaction strip whose face and
  caption react to what just happened when the child runs their code
  (lesson_screen_flet.py).
- build_codey_companion(): the bigger Hub/Dashboard/Map presence -- a
  chunky face disc with a speech bubble carrying a context line ("Day 5
  streak! Ready for today's mission?"), an idle float (motion_flet.bob)
  and a cheer() for celebrations.

Emoji-only, no custom art assets, consistent with how the rest of the app
already communicates everything (rewards, errors, hints) through emoji +
short text rather than illustrations. Flet only, per the phase 7/8
CTk-parity decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import flet as ft

from app.ui.color_utils import with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import accent_gradient, lip_shadow, soft_shadow
from app.ui.theme_flet import scaled


class CodeyState:
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BLOCKED = "blocked"


# (face emoji, caption) per state. Kept short and encouraging, matching the
# tone of the rest of the app's output messages -- Codey reacts to the
# same result, it doesn't replace the existing friendly-error/output text.
_EXPRESSIONS: dict[str, tuple[str, str]] = {
    CodeyState.IDLE: ("🤖", "Ready when you are!"),
    CodeyState.RUNNING: ("💭", "Thinking..."),
    CodeyState.SUCCESS: ("🎉", "Awesome job!"),
    CodeyState.WARNING: ("🤔", "So close -- try again!"),
    CodeyState.ERROR: ("😵", "Uh oh, something broke!"),
    CodeyState.BLOCKED: ("🙅", "Can't do that one yet!"),
}


@dataclass
class CodeyHandle:
    control: ft.Control
    face_text: ft.Text
    caption_text: ft.Text
    set_state: Callable[[str], None]


def build_codey_avatar(theme, scale: float = 1.0) -> CodeyHandle:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    idle_face, idle_caption = _EXPRESSIONS[CodeyState.IDLE]
    face_text = ft.Text(idle_face, size=fs(28))
    caption_text = ft.Text(idle_caption, size=fs(12), color=theme.text_muted, italic=True)

    face_container = ft.Container(
        content=face_text, bgcolor=theme.bg, border_radius=50, width=48, height=48,
        alignment=ft.alignment.Alignment.CENTER,
    )

    control = ft.Row(
        [
            face_container,
            ft.Column(
                [
                    ft.Text("Codey", size=fs(11), weight=ft.FontWeight.BOLD, color=theme.text_muted),
                    caption_text,
                ],
                spacing=0,
            ),
        ],
        spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def set_state(state: str) -> None:
        emoji, caption = _EXPRESSIONS.get(state, _EXPRESSIONS[CodeyState.IDLE])
        face_text.value = emoji
        caption_text.value = caption

    return CodeyHandle(control=control, face_text=face_text, caption_text=caption_text, set_state=set_state)


# -- the companion (Hub / Dashboard / Map) -------------------------------------------
@dataclass
class CompanionHandle:
    control: ft.Control
    face_disc: ft.Control
    """The animated Stack (face disc + accessory badge)."""
    face_text: ft.Text
    line_text: ft.Text
    set_line: Callable[[str], None]
    cheer: Callable[[object], bool]
    """cheer(page): switch to the celebrating face + a quick pulse. Returns
    whether the pulse could be scheduled (see motion_flet.schedule)."""


def build_codey_companion(
    theme, scale: float, line: str, *, page: Optional[object] = None, face: str = "🤖",
    accessory: str = "",
) -> CompanionHandle:
    """Codey as a guide: big face disc on the left, speech bubble on the
    right. Pass `page` to start the idle float straight away (bounded --
    see motion_flet); without it (tests) the companion is static.
    `accessory` (see app/engine/titles.py's LevelTitle.codey_accessory) is
    worn as a small badge on the disc -- Codey "evolves" with the player's
    level."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    face_text = ft.Text(face, size=fs(34), text_align=ft.TextAlign.CENTER)
    accessory_text = ft.Text(accessory, size=fs(16), text_align=ft.TextAlign.CENTER)
    disc = ft.Container(
        content=face_text, width=64, height=64, border_radius=32,
        gradient=accent_gradient(theme.primary),
        shadow=lip_shadow(theme.primary, depth=4),
        alignment=ft.alignment.Alignment.CENTER,
    )
    accessory_badge = ft.Container(
        content=accessory_text, width=28, height=28, border_radius=14,
        bgcolor=theme.card, alignment=ft.alignment.Alignment.CENTER,
        shadow=soft_shadow(opacity=0.2, blur=6, dy=2),
        right=-4, top=-6, visible=bool(accessory),
        data={"kind": "codey_accessory", "accessory": accessory},
    )
    face_disc = ft.Stack([disc, accessory_badge], width=64, height=64)
    motion.prepare_bob(face_disc)

    line_text = ft.Text(line, size=fs(14), weight=ft.FontWeight.BOLD, color=theme.text)
    bubble = ft.Container(
        content=ft.Column(
            [ft.Text("Codey says", size=fs(10), color=theme.text_muted), line_text],
            spacing=2,
        ),
        bgcolor=with_alpha(theme.card, 0.92), border_radius=18,
        padding=ft.padding.Padding.symmetric(horizontal=14, vertical=10),
        shadow=soft_shadow(opacity=0.12, blur=12, dy=4),
        # expand=True bounds the bubble to the Row's remaining width so a
        # long line wraps instead of overflowing past the screen edge.
        expand=True,
    )
    control = ft.Row(
        [face_disc, bubble], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        data={"kind": "codey_companion"},
    )

    def set_line(text: str) -> None:
        line_text.value = text

    def cheer(target_page) -> bool:
        face_text.value = _EXPRESSIONS[CodeyState.SUCCESS][0]
        motion.prepare_pulse(face_disc)
        return motion.pulse(target_page, face_disc, times=2, big=1.15)

    if page is not None:
        motion.bob(page, face_disc)

    return CompanionHandle(
        control=control, face_disc=face_disc, face_text=face_text, line_text=line_text,
        set_line=set_line, cheer=cheer,
    )
