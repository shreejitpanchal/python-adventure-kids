"""Owns the live CTkToplevel + Canvas that a graphical lesson's code draws into."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from app.games.game_canvas import GameCanvas

DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 400


class GameWindow:
    def __init__(self, parent, on_close: Optional[Callable[[], None]] = None):
        self.toplevel = ctk.CTkToplevel(parent)
        self.toplevel.title("Your Game")
        self.toplevel.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.toplevel.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._on_close = on_close
        self._closed = False

        self.canvas_widget = tk.Canvas(
            self.toplevel, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
            bg="white", highlightthickness=0,
        )
        self.canvas_widget.pack(fill="both", expand=True)

        self.game_canvas = GameCanvas(self.canvas_widget, self.toplevel)

    def _handle_close(self) -> None:
        if self._on_close:
            self._on_close()
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self.toplevel.destroy()
        except tk.TclError:
            pass
