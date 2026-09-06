"""Settings screen: pick a color theme from a set of pre-baked presets.

Layout note: uses a wrapping Row of fixed-width cards rather than
ResponsiveRow -- see app/ui/dashboard_flet.py's module docstring for why
(expand=True / ResponsiveRow columns currently render incorrectly in this
Flet version)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import flet as ft

from app.progress.store import InvalidProgressFile
from app.ui.app_state_flet import AppState
from app.ui.theme_flet import FONT_FAMILY_PRESETS, THEME_PRESETS, ThemePreset, scaled
from app.version import get_version_label


def build_settings_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/hub"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            # expand=True lets the title wrap onto a second line at large
            # font scales instead of overflowing past the screen edge.
            ft.Text("⚙️ Settings", size=fs(26), weight=ft.FontWeight.BOLD, color=theme.primary, expand=True),
        ],
        spacing=16,
    )

    return ft.View(
        route="/settings",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        # Extra bottom clearance so the last control isn't hidden behind
        # Android's gesture/navigation bar -- see learning_hub_flet.py's
        # build_learning_hub_view() for the full rationale.
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=[
            header, _build_sound_card(page, state), _build_font_card(page, state),
            _build_theme_card(page, state), _build_progress_card(page, state),
            _build_version_row(state), ft.Container(height=16),
        ],
    )


def _export_filename() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"python_adventure_progress_{stamp}.json"


def _build_progress_card(page: ft.Page, state: AppState) -> ft.Control:
    """Export/import all progress as one JSON file. Export offers a plain
    "save to device" file dialog on desktop, plus a native platform Share
    sheet choice on mobile (Flet's Share service) so the file can be handed
    off to whichever app the user picks there (mail, cloud storage, etc.)
    -- there's no way to target one specific app directly, so this hands
    the choice to the OS's own share sheet rather than assuming one.

    ft.FilePicker/ft.Share are constructed fresh inside each handler,
    never held on AppState or added to page.overlay: both are Service
    controls that self-register with the current page via Service.init()'s
    context.page._services.register_service() the moment they're
    constructed inside a running page session. Persisting one instance and
    adding it to page.overlay -- the pattern used for visual overlay
    controls like SnackBar -- is a different, older registration path that
    doesn't apply to Service controls, and is what rendered as an "Unknown
    control: FilePicker" error on Android instead of actually working.

    Reading/writing by bytes (src_bytes= on save, with_data=True + .bytes
    on pick) rather than by filesystem path matters specifically on
    Android: the paths a native picker/share sheet hands back there are
    often content:// URIs under scoped storage, not plain paths a bare
    open() call can read -- Flet's own file transfer over src_bytes/.bytes
    sidesteps that entirely, and works identically on desktop too.
    """
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    status_text = ft.Text("", size=fs(13), color=theme.success)

    def set_status(message: str, is_error: bool = False) -> None:
        status_text.value = message
        status_text.color = theme.danger if is_error else theme.success
        page.update()

    async def save_export_to_device(payload: bytes, filename: str) -> None:
        picker = ft.FilePicker()
        try:
            saved_path = await picker.save_file(
                dialog_title="Export Progress", file_name=filename, src_bytes=payload,
            )
        except Exception as exc:  # native dialogs can raise platform-specific errors
            set_status(f"Export failed: {exc}", is_error=True)
            return
        set_status(f"Saved to {saved_path}." if saved_path else "Export cancelled.")

    async def share_export(payload: bytes, filename: str) -> None:
        sharer = ft.Share()
        try:
            result = await sharer.share_files(
                [ft.ShareFile.from_bytes(payload, mime_type="application/json", name=filename)],
                subject="Python Adventure progress backup",
                text="Attached: a Python Adventure progress export.",
            )
        except Exception as exc:
            set_status(f"Share failed: {exc}", is_error=True)
            return
        set_status("Shared." if result.status == ft.ShareResultStatus.SUCCESS else "Share cancelled.")

    def show_mobile_export_choice(payload: bytes, filename: str) -> None:
        def close(e=None) -> None:
            page.pop_dialog()

        def choose_save(e=None) -> None:
            close()
            page.run_task(save_export_to_device, payload, filename)

        def choose_share(e=None) -> None:
            close()
            page.run_task(share_export, payload, filename)

        page.show_dialog(ft.AlertDialog(
            modal=False,
            title=ft.Text("Export Progress"),
            content=ft.Text(
                "Save the backup file on this device, or share it through any app that "
                "accepts files."
            ),
            actions=[
                ft.TextButton("Save to Device", on_click=choose_save),
                ft.TextButton("Share…", on_click=choose_share),
                ft.TextButton("Cancel", on_click=close),
            ],
        ))

    async def on_export(e: ft.ControlEvent) -> None:
        payload = json.dumps(state.progress.export_progress_data(), indent=2).encode("utf-8")
        filename = _export_filename()
        if page.platform.is_mobile():
            show_mobile_export_choice(payload, filename)
        else:
            await save_export_to_device(payload, filename)

    async def on_import(e: ft.ControlEvent) -> None:
        picker = ft.FilePicker()
        try:
            files = await picker.pick_files(
                dialog_title="Import Progress",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json"],
                with_data=True,
            )
        except Exception as exc:
            set_status(f"Import failed: {exc}", is_error=True)
            return
        if not files:
            return
        picked = files[0]
        try:
            raw = picked.bytes
            if raw is None:
                raise ValueError("the selected file couldn't be read")
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            set_status(f"Couldn't read file: {exc}", is_error=True)
            return
        _confirm_import(page, state, data, status_text)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("💾 Progress", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Save your progress to a file, or load progress from a file you exported before.",
                    size=fs(13), color=theme.text_muted,
                ),
                ft.Row(
                    [
                        ft.Button(
                            "⬇️ Export Progress", on_click=on_export, height=44,
                            style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                        ),
                        ft.Button(
                            "⬆️ Import Progress", on_click=on_import, height=44,
                            style=ft.ButtonStyle(bgcolor=theme.danger, color="#FFFFFF"),
                        ),
                    ],
                    wrap=True, spacing=8,
                ),
                status_text,
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _confirm_import(page: ft.Page, state: AppState, data: dict, status_text: ft.Text) -> None:
    theme = state.theme

    def cancel(e=None) -> None:
        page.pop_dialog()

    def do_import(e=None) -> None:
        try:
            state.progress.import_progress_data(data)
        except InvalidProgressFile as exc:
            page.pop_dialog()
            status_text.value = str(exc)
            status_text.color = theme.danger
            page.update()
            return
        page.pop_dialog()
        status_text.value = "Progress imported successfully."
        status_text.color = theme.success
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Import progress?"),
        content=ft.Text(
            "Importing will replace ALL current progress with the data from this file. "
            "This can't be undone."
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel),
            ft.TextButton("Import & Overwrite", on_click=do_import, style=ft.ButtonStyle(color=theme.danger)),
        ],
    )
    page.show_dialog(dialog)


def _build_version_row(state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    return ft.Container(
        content=ft.Text(
            get_version_label(), size=fs(14), weight=ft.FontWeight.BOLD,
            color=theme.text, text_align=ft.TextAlign.CENTER,
        ),
        bgcolor=theme.card, border_radius=12, padding=12, margin=ft.margin.Margin.symmetric(vertical=8),
        alignment=ft.alignment.Alignment.CENTER,
    )


def _build_sound_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    def on_toggle(e: ft.ControlEvent) -> None:
        state.settings.sound_enabled = e.control.value
        state.save_settings()

    # Not expand=True + MainAxisAlignment.SPACE_BETWEEN to push the switch
    # to the far edge -- see dashboard_flet.py's module docstring and the
    # parent dashboard's summary-row code for why both of those layout
    # tricks are unreliable in this Flet version; a plain spaced Row is
    # the pattern already proven to work everywhere else in this app.
    return ft.Container(
        content=ft.Row(
            [
                ft.Text("🔊 Sound Effects", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Switch(value=state.settings.sound_enabled, on_change=on_toggle, active_color=theme.primary),
            ],
            spacing=16,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


_FONT_SIZE_LABELS = {"small": "Small", "medium": "Medium", "large": "Large", "extra_large": "Extra Large"}
_FONT_FAMILY_LABELS = {"default": "Playful", "classic": "Classic"}


def _build_font_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    def select(family_key: str | None = None, size_key: str | None = None):
        def handler(_e=None) -> None:
            state.apply_font(
                family_key or state.settings.font_family,
                size_key or state.settings.font_size,
            )
            # Same rebuild-in-place pattern as the theme card's select() --
            # see its comment for why page.go("/settings") wouldn't repaint.
            page.views.clear()
            page.views.append(build_settings_view(page, state))
            page.theme = ft.Theme(font_family=state.font_family)
            page.dark_theme = ft.Theme(font_family=state.font_family)
            page.update()
        return handler

    current_size = state.settings.font_size
    size_buttons = [
        ft.Button(
            label, on_click=select(size_key=key), height=40,
            disabled=current_size == key,
            style=ft.ButtonStyle(
                bgcolor=theme.primary if current_size == key else theme.text_muted, color="#FFFFFF",
            ),
        )
        for key, label in _FONT_SIZE_LABELS.items()
    ]

    current_family = state.settings.font_family
    family_buttons = [
        ft.Button(
            label, on_click=select(family_key=key), height=40,
            disabled=current_family == key,
            style=ft.ButtonStyle(
                bgcolor=theme.primary if current_family == key else theme.text_muted, color="#FFFFFF",
                text_style=ft.TextStyle(font_family=FONT_FAMILY_PRESETS[key]),
            ),
        )
        for key, label in _FONT_FAMILY_LABELS.items()
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("🔤 Text Size & Font", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Make text bigger or change the style — great for reading on a tablet.",
                    size=fs(13), color=theme.text_muted,
                ),
                ft.Text("Size", size=fs(13), color=theme.text_muted),
                ft.Row(size_buttons, wrap=True, spacing=8),
                ft.Text("Style", size=fs(13), color=theme.text_muted),
                ft.Row(family_buttons, wrap=True, spacing=8),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _build_theme_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    current_key = state.settings.theme
    player_level = state.progress.get_player_level().level

    options = [
        _build_theme_option(page, state, preset, current_key == preset.key, player_level >= preset.min_level)
        for preset in THEME_PRESETS.values()
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("🎨 Choose a Theme", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Pick the colors you like best — you can change this anytime.",
                    size=fs(13), color=theme.text_muted,
                ),
                ft.Row(options, wrap=True, spacing=16, run_spacing=16),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _build_theme_option(
    page: ft.Page, state: AppState, preset: ThemePreset, is_selected: bool, unlocked: bool,
) -> ft.Control:
    def select(_e=None) -> None:
        if state.progress.get_player_level().level < preset.min_level:
            return  # defense in depth -- the button should already be disabled
        state.apply_theme(preset.key)
        # Not page.go("/settings") -- Flet's own routing drops a RouteChangeEvent
        # whose route matches the last-seen one (Page.before_event(), page.py),
        # so navigating to the route we're already on is a silent no-op: the
        # view stays built with the old theme's colors until some other route
        # actually changes. Rebuild the view and reapply the page-level theme
        # bits in place instead, the same way app_window_flet.route_change() does.
        page.views.clear()
        page.views.append(build_settings_view(page, state))
        page.bgcolor = state.theme.bg
        page.theme_mode = ft.ThemeMode.DARK if state.theme.is_dark else ft.ThemeMode.LIGHT
        page.update()

    swatch_colors = (
        (preset.primary, preset.success, preset.warning, preset.danger) if unlocked
        else (preset.text_muted,) * 4
    )
    swatches = ft.Row(
        [ft.Container(bgcolor=color, width=28, height=28, border_radius=8) for color in swatch_colors],
        spacing=6,
    )

    if not unlocked:
        button_text = f"🔒 Unlocks at Level {preset.min_level}"
    else:
        button_text = "✅ Selected" if is_selected else "Select"

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"{preset.icon}  {preset.title}" if unlocked else f"🔒  {preset.title}",
                    size=scaled(16, state.font_scale), weight=ft.FontWeight.BOLD,
                    color=preset.text if unlocked else preset.text_muted,
                ),
                swatches,
                ft.Button(
                    button_text,
                    disabled=is_selected or not unlocked, on_click=select, height=48,
                    style=ft.ButtonStyle(bgcolor=preset.primary if unlocked else preset.text_muted, color="#FFFFFF"),
                ),
            ],
            spacing=10,
        ),
        bgcolor=preset.bg, border_radius=16, padding=16, width=260,
        border=ft.border.Border.all(3, state.theme.primary if is_selected else preset.card),
    )
