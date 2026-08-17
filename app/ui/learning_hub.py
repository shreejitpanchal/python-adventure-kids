"""Learning Hub: the very first screen a child sees after setup -- four ways
to reach content (guided path, two Code Cracker tracks, projects), replacing
the old "land straight on the Dashboard" behavior. The Dashboard (Today's
Mission) is now one of the four destinations, not the top of the navigation
hierarchy -- see app_window.py's _route_initial_screen(). Settings and
Parent Area live here too (in the header), not on the Dashboard -- this is
the true top of the hierarchy, so they only need one home.

All status text is computed once by app.engine.hub_status.compute_hub_status()
and just rendered here -- this screen never recomputes progress numbers
itself, matching the "status text lives in one shared place" rule that keeps
the CTk and Flet Hub screens in sync.
"""
from __future__ import annotations

import customtkinter as ctk

from app.engine.hub_status import compute_hub_status
from app.ui import theme
from app.ui.assets import make_ctk_icon
from app.ui.color_utils import contrasting_text_color, darken

# Card key -> a settings.preferred_learning_mode value that should surface
# that card first.
_MODE_TO_CARD_KEY: dict[str, str] = {
    "guided": "guided",
    "projects": "projects",
    "crackers": "code_crackers",
    "advanced": "advanced_code_crackers",
}


class HubFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        # Card definitions built per-instance (not at class scope) since
        # each entry's "navigate" closure needs to call methods on this
        # particular app instance.
        self._card_defs = [
            {
                "key": "guided",
                "title": "🚀 Start Learning Python",
                "subtitle": "A guided path for beginners. Continue your next lesson.",
                "status_attr": "guided_status",
                "color": "#4C97FF",
                "navigate": lambda: app.show_dashboard(),
            },
            {
                "key": "code_crackers",
                "title": "🐛 Fix Code Cracker Puzzles",
                "subtitle": "Find and fix bugs in short Python programs.",
                "status_attr": "cracker_status",
                "color": "#D4A017",
                "navigate": lambda: app.show_category_levels("code_crackers"),
            },
            {
                "key": "advanced_code_crackers",
                "title": "🧠 Advanced Code Crackers",
                "subtitle": "Tricky real-world Python bugs for experienced coders.",
                "status_attr": "advanced_cracker_status",
                "color": "#37474F",
                "navigate": lambda: app.show_category_levels("advanced_code_crackers"),
            },
            {
                "key": "projects",
                "title": "🛠️ Build a Project",
                "subtitle": "Games, art, adventures, and coding challenges.",
                "status_attr": "project_status",
                "color": "#EF5350",
                "navigate": lambda: app.show_project_categories(),
            },
        ]
        self._cards_by_key = {card["key"]: card for card in self._card_defs}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.hub_status = compute_hub_status(app.lesson_engine, app.progress, app.settings)

        self._build_header(self.scroll)
        self._build_resume_banner(self.scroll)
        self._build_cards(self.scroll)

    # -- header (no "Menu" button -- this IS the menu / top of the hierarchy) --
    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))

        # Kept as an attribute so the underlying image isn't garbage-collected.
        self.icon_image = make_ctk_icon(size=40)
        ctk.CTkLabel(
            header, text=" Python Adventure", image=self.icon_image, compound="left",
            font=theme.font_title(30), text_color=theme.COLOR_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header, text="👋 Parent Area", font=theme.font_body(13), width=140, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._open_parent_area,
        ).pack(side="right")

        ctk.CTkButton(
            header, text="⚙️ Settings", font=theme.font_body(13), width=120, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._open_settings,
        ).pack(side="right", padx=(0, 10))

        name = self.app.settings.child_name or "Explorer"
        ctk.CTkLabel(
            parent, text=f"Welcome back, {name}!", font=theme.font_heading(20),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=44, pady=(0, 20))

    # -- optional "continue where you left off" banner --------------------------
    def _build_resume_banner(self, parent) -> None:
        if self.hub_status.resume_label is None:
            return

        ctk.CTkButton(
            parent, text=f"↩️  {self.hub_status.resume_label}", font=theme.font_body(15),
            anchor="w", height=48, corner_radius=14,
            fg_color=theme.COLOR_CARD, hover_color=darken(theme.COLOR_CARD),
            text_color=theme.COLOR_TEXT,
            command=self._on_resume,
        ).pack(fill="x", padx=40, pady=(0, 20))

    def _on_resume(self) -> None:
        route = self.app.settings.last_learning_route
        card = self._cards_by_key.get(route)
        if card is not None:
            card["navigate"]()

    # -- the five cards -----------------------------------------------------------
    def _build_cards(self, parent) -> None:
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        preferred_mode = self.app.settings.preferred_learning_mode or "guided"
        preferred_key = _MODE_TO_CARD_KEY.get(preferred_mode, "guided")

        # Stable sort: the preferred card moves to the front, everything else
        # keeps its fixed relative order from _card_defs.
        ordered = sorted(self._card_defs, key=lambda c: 0 if c["key"] == preferred_key else 1)

        for card in ordered:
            self._build_card(body, card, emphasized=card["key"] == preferred_key)

    def _build_card(self, parent, card: dict, emphasized: bool) -> None:
        status = getattr(self.hub_status, card["status_attr"])
        color = card["color"]

        height = 108 if emphasized else 84
        title_size = 22 if emphasized else 18

        ctk.CTkButton(
            parent,
            text=f"{card['title']}\n{card['subtitle']}\n{status}",
            font=theme.font_heading(title_size), anchor="w", height=height, corner_radius=18,
            fg_color=color, hover_color=darken(color),
            text_color=contrasting_text_color(color),
            command=lambda c=card: self._on_open_card(c),
        ).pack(fill="x", pady=10)

    def _on_open_card(self, card: dict) -> None:
        self.app.settings.last_learning_route = card["key"]
        self.app.save_settings()
        card["navigate"]()

    def _open_parent_area(self) -> None:
        from app.parent.dashboard import open_parent_area

        open_parent_area(self.app)

    def _open_settings(self) -> None:
        self.app.show_settings()
