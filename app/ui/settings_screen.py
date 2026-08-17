"""Settings screen: pick a color theme from a set of pre-baked presets."""
from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.version import get_version_label


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_sound_card()
        self._build_font_card()
        self._build_theme_card()
        self._build_version_label()

    def _build_sound_card(self) -> None:
        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=20)
        card.pack(fill="x", pady=(0, 20))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=20)

        ctk.CTkLabel(
            row, text="🔊 Sound Effects", font=theme.font_heading(20),
            text_color=theme.COLOR_TEXT,
        ).pack(side="left")

        self._sound_switch = ctk.CTkSwitch(
            row, text="", onvalue=True, offvalue=False,
            progress_color=theme.COLOR_PRIMARY, command=self._on_toggle_sound,
        )
        self._sound_switch.pack(side="right")
        if self.app.settings.sound_enabled:
            self._sound_switch.select()
        else:
            self._sound_switch.deselect()

    def _on_toggle_sound(self) -> None:
        self.app.settings.sound_enabled = bool(self._sound_switch.get())
        self.app.save_settings()

    _FONT_SIZE_LABELS = {"small": "Small", "medium": "Medium", "large": "Large", "extra_large": "Extra Large"}
    _FONT_FAMILY_LABELS = {"default": "Playful", "classic": "Classic", "clean": "Clean"}

    def _build_font_card(self) -> None:
        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=20)
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card, text="🔤 Text Size & Font", font=theme.font_heading(20),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            card, text="Make text bigger or change the style — great for reading on a tablet.",
            font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            card, text="Size", font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24)

        size_row = ctk.CTkFrame(card, fg_color="transparent")
        size_row.pack(fill="x", padx=24, pady=(4, 16))
        current_size = self.app.settings.font_size
        for size_key, label in self._FONT_SIZE_LABELS.items():
            is_selected = current_size == size_key
            ctk.CTkButton(
                size_row, text=label, font=theme.font_body(13), height=36,
                fg_color=theme.COLOR_PRIMARY if is_selected else theme.COLOR_TEXT_MUTED,
                hover_color=theme.COLOR_PRIMARY_HOVER,
                state="disabled" if is_selected else "normal",
                command=lambda key=size_key: self._on_select_font(size_key=key),
            ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            card, text="Style", font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24)

        family_row = ctk.CTkFrame(card, fg_color="transparent")
        family_row.pack(fill="x", padx=24, pady=(4, 20))
        current_family = self.app.settings.font_family
        for family_key, label in self._FONT_FAMILY_LABELS.items():
            is_selected = current_family == family_key
            ctk.CTkButton(
                family_row, text=label,
                font=ctk.CTkFont(family=theme.FONT_FAMILY_PRESETS[family_key], size=14), height=36,
                fg_color=theme.COLOR_PRIMARY if is_selected else theme.COLOR_TEXT_MUTED,
                hover_color=theme.COLOR_PRIMARY_HOVER,
                state="disabled" if is_selected else "normal",
                command=lambda key=family_key: self._on_select_font(family_key=key),
            ).pack(side="left", padx=(0, 8))

    def _on_select_font(self, family_key: str | None = None, size_key: str | None = None) -> None:
        self.app.apply_and_persist_font(
            family_key or self.app.settings.font_family,
            size_key or self.app.settings.font_size,
        )
        self.app.show_settings()

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

        player_level = self.app.progress.get_player_level().level
        current_key = self.app.settings.theme
        for index, preset in enumerate(theme.THEME_PRESETS.values()):
            row, col = divmod(index, 2)
            unlocked = player_level >= preset.min_level
            self._build_theme_option(grid, preset, current_key == preset.key, unlocked, row, col)

    def _build_theme_option(self, parent, preset, is_selected: bool, unlocked: bool, row: int, col: int) -> None:
        border_color = theme.COLOR_PRIMARY if is_selected else preset.card
        option = ctk.CTkFrame(
            parent, fg_color=preset.bg, corner_radius=16,
            border_width=3, border_color=border_color,
        )
        option.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        title_text = f"{preset.icon}  {preset.title}" if unlocked else f"🔒  {preset.title}"
        ctk.CTkLabel(
            option, text=title_text, font=theme.font_heading(16),
            text_color=preset.text if unlocked else preset.text_muted,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        swatches = ctk.CTkFrame(option, fg_color="transparent")
        swatches.pack(anchor="w", padx=16, pady=(0, 12))
        swatch_colors = (
            (preset.primary, preset.success, preset.warning, preset.danger) if unlocked
            else (preset.text_muted,) * 4
        )
        for color in swatch_colors:
            ctk.CTkFrame(
                swatches, fg_color=color, width=28, height=28, corner_radius=8,
            ).pack(side="left", padx=(0, 6))

        if not unlocked:
            button_text = f"🔒 Unlocks at Level {preset.min_level}"
        else:
            button_text = "✅ Selected" if is_selected else "Select"
        ctk.CTkButton(
            option, text=button_text, font=theme.font_body(13), height=34,
            fg_color=preset.primary if unlocked else theme.COLOR_TEXT_MUTED,
            hover_color=preset.primary_hover,
            text_color="#FFFFFF", state="disabled" if (is_selected or not unlocked) else "normal",
            command=lambda key=preset.key: self._on_select_theme(key),
        ).pack(fill="x", padx=16, pady=(0, 16))

    def _on_select_theme(self, theme_key: str) -> None:
        preset = theme.THEME_PRESETS.get(theme_key)
        if preset is None:
            return
        if self.app.progress.get_player_level().level < preset.min_level:
            return  # defense in depth -- the button should already be disabled
        self.app.apply_and_persist_theme(theme_key)
        self.app.show_settings()

    def _build_version_label(self) -> None:
        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=12)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            card, text=get_version_label(), font=theme.font_heading(14),
            text_color=theme.COLOR_TEXT,
        ).pack(pady=10)

    def _on_menu(self) -> None:
        self.app.show_hub()
