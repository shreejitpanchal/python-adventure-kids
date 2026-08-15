"""Codey the Robot -- a small companion avatar whose face and caption react
to what just happened when the child runs their code. Emoji-only, no custom
art assets, consistent with how the rest of the app already communicates
everything (rewards, errors, hints) through emoji + short text rather than
illustrations. Flet only, per the phase 7/8 CTk-parity decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft


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


def build_codey_avatar(theme) -> CodeyHandle:
    idle_face, idle_caption = _EXPRESSIONS[CodeyState.IDLE]
    face_text = ft.Text(idle_face, size=28)
    caption_text = ft.Text(idle_caption, size=12, color=theme.text_muted, italic=True)

    face_container = ft.Container(
        content=face_text, bgcolor=theme.bg, border_radius=50, width=48, height=48,
        alignment=ft.alignment.Alignment.CENTER,
    )

    control = ft.Row(
        [
            face_container,
            ft.Column(
                [
                    ft.Text("Codey", size=11, weight=ft.FontWeight.BOLD, color=theme.text_muted),
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
