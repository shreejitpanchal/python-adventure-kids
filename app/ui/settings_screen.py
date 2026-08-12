"""Settings screen: pick a color theme from a set of pre-baked presets."""
from __future__ import annotations

import customtkinter as ctk

from app.ui import theme


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_theme_card()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 16))

        ctk.CTkButton(
            header, text="🏠 Menu", font=theme.font_body(14), width=100, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_menu,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="⚙️ Settings", font=theme.font_title(26),
            text_color=theme.COLOR_PRIMARY,
        ).pack(side="left", padx=20)

    def _build_theme_card(self) -> None:
        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=20)
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="🎨 Choose a Theme", font=theme.font_heading(20),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            card, text="Pick the colors you like best — you can change this anytime.",
            font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 16))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=(0, 24))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        current_key = self.app.settings.theme
        for index, preset in enumerate(theme.THEME_PRESETS.values()):
            row, col = divmod(index, 2)
            self._build_theme_option(grid, preset, current_key == preset.key, row, col)

    def _build_theme_option(self, parent, preset, is_selected: bool, row: int, col: int) -> None:
        border_color = theme.COLOR_PRIMARY if is_selected else preset.card
        option = ctk.CTkFrame(
            parent, fg_color=preset.bg, corner_radius=16,
            border_width=3, border_color=border_color,
        )
        option.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        ctk.CTkLabel(
            option, text=f"{preset.icon}  {preset.title}", font=theme.font_heading(16),
            text_color=preset.text,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        swatches = ctk.CTkFrame(option, fg_color="transparent")
        swatches.pack(anchor="w", padx=16, pady=(0, 12))
        for color in (preset.primary, preset.success, preset.warning, preset.danger):
            ctk.CTkFrame(
                swatches, fg_color=color, width=28, height=28, corner_radius=8,
            ).pack(side="left", padx=(0, 6))

        button_text = "✅ Selected" if is_selected else "Select"
        ctk.CTkButton(
            option, text=button_text, font=theme.font_body(13), height=34,
            fg_color=preset.primary, hover_color=preset.primary_hover,
            text_color="#FFFFFF", state="disabled" if is_selected else "normal",
            command=lambda key=preset.key: self._on_select_theme(key),
        ).pack(fill="x", padx=16, pady=(0, 16))

    def _on_select_theme(self, theme_key: str) -> None:
        self.app.apply_and_persist_theme(theme_key)
        self.app.show_settings()

    def _on_menu(self) -> None:
        self.app.show_dashboard()
