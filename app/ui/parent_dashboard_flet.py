"""PIN-gated parent area: progress summary and basic controls.

Ported from app/parent/dashboard.py. The old CTk version opened two
nested CTkToplevel popups (a PIN prompt, then a summary/activity/reset
window) -- Android has no equivalent of a second OS window, so this is a
full redesign, not a like-for-like port: a single /parent route that
internally swaps between a PIN-entry step and the summary step (the same
mutable-body pattern setup_wizard_flet.py uses for its steps), with the
reset confirmation shown as a page.show_dialog(ft.AlertDialog(...)) modal
instead of a third nested popup.
"""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState

EVENT_ICONS = {
    "lesson_completed": "✅",
    "badge_earned": "🎖️",
    "attempt_error": "🐞",
    "attempt_blocked": "🚫",
    "attempt_timeout": "⏳",
    "attempt_wrong_output": "🔁",
    "hint_used": "💡",
}

EVENT_LABELS = {
    "lesson_completed": "Completed a lesson",
    "badge_earned": "Earned a badge",
    "attempt_error": "Got an error",
    "attempt_blocked": "Tried something blocked",
    "attempt_timeout": "Code took too long",
    "attempt_wrong_output": "Output didn't match yet",
    "hint_used": "Used a hint",
}


def build_parent_view(page: ft.Page, state: AppState) -> ft.View:
    return _ParentController(page, state).build_view()


class _ParentController:
    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.theme = state.theme
        self.body = ft.Column(spacing=16)
        self.value_texts: dict[str, ft.Text] = {}

    def build_view(self) -> ft.View:
        if self.state.settings.has_parent_pin():
            self._show_pin_step()
        else:
            self._show_summary_step()

        return ft.View(
            route="/parent",
            bgcolor=self.theme.bg,
            scroll=ft.ScrollMode.AUTO,
            padding=24,
            controls=[self.body],
        )

    def _set(self, controls: list[ft.Control]) -> None:
        self.body.controls = controls
        self.page.update()

    def _menu_row(self) -> ft.Control:
        return ft.Row(
            [ft.Button(
                "🏠 Menu", on_click=self._on_menu, height=48,
                style=ft.ButtonStyle(bgcolor=self.theme.text_muted, color="#FFFFFF"),
            )],
        )

    # -- PIN step -------------------------------------------------------------
    def _show_pin_step(self) -> None:
        theme = self.theme
        self.pin_field = ft.TextField(
            hint_text="••••", width=200, text_align=ft.TextAlign.CENTER,
            password=True, max_length=4, autofocus=True,
        )
        self.pin_error_text = ft.Text("", size=13, color=theme.danger)
        self.pin_field.on_submit = self._submit_pin

        self._set([
            self._menu_row(),
            ft.Row([
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🔒 Parent Area", size=22, weight=ft.FontWeight.BOLD, color=theme.text),
                            ft.Text("Enter the 4-digit PIN", size=14, color=theme.text_muted),
                            self.pin_field,
                            self.pin_error_text,
                            ft.Button(
                                "Unlock", on_click=self._submit_pin, height=48,
                                style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
                    ),
                    bgcolor=theme.card, border_radius=18, padding=40, width=380,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ])

    def _submit_pin(self, e=None) -> None:
        if self.state.settings.verify_parent_pin((self.pin_field.value or "").strip()):
            self._show_summary_step()
        else:
            self.pin_error_text.value = "Incorrect PIN."
            self.pin_field.value = ""
            self.page.update()

    # -- summary step -----------------------------------------------------------
    def _show_summary_step(self) -> None:
        theme = self.theme
        summary = self.state.progress.get_summary()
        child_name = self.state.settings.child_name or "Your child"

        rows = [
            ("child", "Child", child_name),
            ("level", "Current level", str(summary.level)),
            ("stars", "Total stars", f"⭐ {summary.total_stars}"),
            ("lessons", "Lessons completed", str(summary.lessons_completed)),
            ("badges", "Badges earned", str(summary.badges_earned)),
            ("streak", "Day streak", str(summary.streak_days)),
        ]
        # A fixed label width (rather than Row(alignment=SPACE_BETWEEN), which
        # doesn't reliably respect the parent's actual width -- see
        # dashboard_flet.py's header for the same lesson learned in Phase 4)
        # keeps the value directly after the label instead of pushed off
        # the edge of a Row wider than its container.
        self.value_texts = {}
        summary_rows: list[ft.Control] = []
        for key, label, value in rows:
            value_text = ft.Text(value, size=15, color=theme.text)
            self.value_texts[key] = value_text
            summary_rows.append(
                ft.Row([ft.Text(label, size=15, color=theme.text_muted, width=180), value_text])
            )

        summary_card = ft.Container(
            content=ft.Column(summary_rows, spacing=10),
            bgcolor=theme.card, border_radius=16, padding=20, width=380,
        )

        self.activity_column = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._refresh_activity()
        activity_card = ft.Container(
            content=self.activity_column, bgcolor=theme.card, border_radius=16, padding=16, height=200,
        )

        self.status_text = ft.Text("", size=13, color=theme.success)

        controls: list[ft.Control] = [
            self._menu_row(),
            ft.Text("👋 Parent Area", size=22, weight=ft.FontWeight.BOLD, color=theme.text),
            ft.Row([summary_card], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("Recent Activity", size=16, weight=ft.FontWeight.BOLD, color=theme.text),
            activity_card,
        ]

        if not self.state.settings.has_parent_pin():
            controls.append(
                ft.Text("No PIN is set yet — anyone can open this area.", size=13, color=theme.warning)
            )

        controls.append(self.status_text)
        controls.append(
            ft.Button(
                "Reset Progress", on_click=self._confirm_reset, height=48,
                style=ft.ButtonStyle(bgcolor=theme.danger, color="#FFFFFF"),
            )
        )

        self._set(controls)

    def _refresh_activity(self) -> None:
        theme = self.theme
        recent = self.state.progress.get_recent_activity(limit=20)
        if not recent:
            self.activity_column.controls = [
                ft.Text(
                    "Nothing yet — activity shows up here once lessons begin.",
                    size=13, color=theme.text_muted,
                )
            ]
        else:
            items: list[ft.Control] = []
            for row in recent:
                icon = EVENT_ICONS.get(row["event_type"], "•")
                label = EVENT_LABELS.get(row["event_type"], row["event_type"])
                lesson_part = f" ({row['lesson_id']})" if row["lesson_id"] else ""
                items.append(ft.Text(f"{icon} {label}{lesson_part}", size=13, color=theme.text))
            self.activity_column.controls = items

    def _refresh_summary_values(self) -> None:
        fresh = self.state.progress.get_summary()
        self.value_texts["level"].value = str(fresh.level)
        self.value_texts["stars"].value = f"⭐ {fresh.total_stars}"
        self.value_texts["lessons"].value = str(fresh.lessons_completed)
        self.value_texts["badges"].value = str(fresh.badges_earned)
        self.value_texts["streak"].value = str(fresh.streak_days)

    # -- reset ------------------------------------------------------------------
    def _confirm_reset(self, e) -> None:
        theme = self.theme
        child_name = self.state.settings.child_name or "your child"

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reset progress?"),
            content=ft.Text(f"Reset all of {child_name}'s progress? This can't be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=self._cancel_reset),
                ft.TextButton("Reset", on_click=self._do_reset, style=ft.ButtonStyle(color=theme.danger)),
            ],
        )
        self.page.show_dialog(dialog)

    def _cancel_reset(self, e=None) -> None:
        self.page.pop_dialog()

    def _do_reset(self, e=None) -> None:
        self.state.progress.reset_progress()
        self._refresh_summary_values()
        self._refresh_activity()
        self.status_text.value = "Progress has been reset."
        self.page.pop_dialog()
        self.page.update()

    def _on_menu(self, e) -> None:
        self.page.go("/dashboard")
