"""Parent area: progress summary and basic controls.

Ported from app/parent/dashboard.py. The old CTk version opened a
CTkToplevel popup; Android has no equivalent of a second OS window, so
this is a full redesign, not a like-for-like port: a single /parent route
showing the summary/activity/reset content directly (the same
mutable-body pattern setup_wizard_flet.py uses for its steps), with the
reset confirmation shown as a page.show_dialog(ft.AlertDialog(...)) modal
instead of a nested popup.

Styled with the game-world kit's header and cards so it matches the rest
of the app, but deliberately without Codey or celebrations -- this screen
is for the parent, and the tone stays calm and factual.
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.engine.titles import level_title
from app.ui.app_state_flet import AppState
from app.ui.components.adventure_kit_flet import hero_header, pill_button, plain_card, scene_view
from app.ui.theme_flet import scaled

EVENT_ICONS = {
    "lesson_completed": "✅",
    "badge_earned": "🎖️",
    "attempt_error": "🐞",
    "attempt_blocked": "🚫",
    "attempt_timeout": "⏳",
    "attempt_wrong_output": "🔁",
    "hint_used": "💡",
    "quiz_completed": "❓",
    "chest_opened": "🎁",
    "quest_bonus_claimed": "🗺️",
}

EVENT_LABELS = {
    "lesson_completed": "Completed a lesson",
    "badge_earned": "Earned a badge",
    "attempt_error": "Got an error",
    "attempt_blocked": "Tried something blocked",
    "attempt_timeout": "Code took too long",
    "attempt_wrong_output": "Output didn't match yet",
    "hint_used": "Used a hint",
    "quiz_completed": "Finished a quiz",
    "chest_opened": "Opened the Daily Treasure",
    "quest_bonus_claimed": "Claimed the daily quest bonus",
}

_CARD_WIDTH = 380


def build_parent_view(page: ft.Page, state: AppState) -> ft.View:
    return _ParentController(page, state).build_view()


class _ParentController:
    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.theme = state.theme
        self.scale = state.font_scale
        self.body = ft.Column(spacing=16)
        self.value_texts: dict[str, ft.Text] = {}

    def _fs(self, base_size: int) -> int:
        """Scaled font size -- see AppState.font_scale / app/ui/theme_flet.py."""
        return scaled(base_size, self.scale)

    def build_view(self) -> ft.View:
        self._show_summary_step()
        return scene_view("/parent", self.theme, [self.body], page=self.page)

    def _set(self, controls: list[ft.Control]) -> None:
        self.body.controls = controls
        self.page.update()

    def _header(self) -> ft.Control:
        return hero_header(
            self.theme, title="👋 Parent Area", scale=self.scale,
            buttons=[pill_button("🏠 Menu", self._on_menu, bgcolor=self.theme.text_muted, color="#FFFFFF")],
        )

    def _label_row(self, label: str, value_text: ft.Text) -> ft.Control:
        # A fixed label width (rather than Row(alignment=SPACE_BETWEEN), which
        # doesn't reliably respect the parent's actual width -- see
        # dashboard_flet.py's header for the same lesson learned in Phase 4)
        # keeps the value directly after the label instead of pushed off
        # the edge of a Row wider than its container.
        return ft.Row([ft.Text(label, size=self._fs(15), color=self.theme.text_muted, width=180), value_text])

    def _card_title(self, text: str) -> ft.Text:
        return ft.Text(text, size=self._fs(18), weight=ft.FontWeight.BOLD, color=self.theme.text)

    # -- summary step -----------------------------------------------------------
    def _show_summary_step(self) -> None:
        theme = self.theme
        summary = self.state.progress.get_summary()
        player = self.state.progress.get_player_level()
        child_name = self.state.settings.child_name or "Your child"

        rows = [
            ("child", "Child", child_name),
            ("level", "Current level", str(summary.level)),
            ("player_level", "Player level", f"{player.level} · {level_title(player.level).title}"),
            ("stars", "Total stars", f"⭐ {summary.total_stars}"),
            ("lessons", "Lessons completed", str(summary.lessons_completed)),
            ("badges", "Badges earned", str(summary.badges_earned)),
            ("streak", "Day streak", str(summary.streak_days)),
        ]
        self.value_texts = {}
        summary_rows: list[ft.Control] = [self._card_title("📋 Summary")]
        for key, label, value in rows:
            value_text = ft.Text(value, size=self._fs(15), color=theme.text)
            self.value_texts[key] = value_text
            summary_rows.append(self._label_row(label, value_text))

        summary_card = plain_card(theme, summary_rows, padding=20, width=_CARD_WIDTH, data={"kind": "parent_summary"})

        rename_card = self._build_rename_card()
        weekly_card = self._build_weekly_card()
        mastery_card = self._build_mastery_card()

        # No scroll=AUTO / fixed height here either -- see _build_mastery_card()'s
        # comment; this card grows naturally as part of the page's own scroll.
        self.activity_column = ft.Column(spacing=4)
        self._refresh_activity()
        activity_card = plain_card(
            theme, [self._card_title("🕒 Recent Activity"), self.activity_column], padding=16,
            data={"kind": "parent_activity"},
        )

        self.status_text = ft.Text("", size=self._fs(13), color=theme.success)

        controls: list[ft.Control] = [
            self._header(),
            ft.Row([summary_card], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([rename_card], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([weekly_card], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([mastery_card], alignment=ft.MainAxisAlignment.CENTER),
            activity_card,
            self.status_text,
            ft.Button(
                "Reset Progress", on_click=self._confirm_reset, height=48,
                style=ft.ButtonStyle(bgcolor=theme.danger, color="#FFFFFF"),
            ),
        ]
        self._set(controls)

    def _build_rename_card(self) -> ft.Control:
        theme = self.theme
        self.rename_field = ft.TextField(
            value=self.state.settings.child_name, width=220, text_align=ft.TextAlign.CENTER,
        )
        self.rename_status_text = ft.Text("", size=self._fs(12), color=theme.success)

        card = plain_card(
            theme,
            [
                self._card_title("✏️ Child's Name"),
                self.rename_field,
                ft.Button(
                    "Save", on_click=self._save_child_name, height=44,
                    style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                ),
                self.rename_status_text,
            ],
            padding=20, width=_CARD_WIDTH, data={"kind": "parent_rename"},
        )
        card.content.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        return card

    def _save_child_name(self, e=None) -> None:
        theme = self.theme
        new_name = (self.rename_field.value or "").strip()
        if not new_name:
            self.rename_status_text.value = "Name can't be empty."
            self.rename_status_text.color = theme.danger
            self.page.update()
            return
        self.state.settings.child_name = new_name
        self.state.save_settings()
        self.value_texts["child"].value = new_name
        self.rename_status_text.value = "Name updated."
        self.rename_status_text.color = theme.success
        self.page.update()

    def _build_weekly_card(self) -> ft.Control:
        theme = self.theme
        weekly = self.state.progress.get_weekly_summary()

        rows = [
            ("lessons", "Lessons completed", str(weekly.lessons_completed)),
            ("stars", "Stars earned", f"⭐ {weekly.stars_earned}"),
            ("quizzes", "Quiz attempts", str(weekly.quiz_attempts)),
            ("badges", "Badges earned", str(weekly.badges_earned)),
            ("active_days", "Active days", f"{weekly.active_days}/7"),
        ]
        self.weekly_value_texts = {}
        weekly_rows: list[ft.Control] = [self._card_title("📅 This Week")]
        for key, label, value in rows:
            value_text = ft.Text(value, size=self._fs(15), color=theme.text)
            self.weekly_value_texts[key] = value_text
            weekly_rows.append(self._label_row(label, value_text))

        return plain_card(theme, weekly_rows, padding=20, width=_CARD_WIDTH, data={"kind": "parent_weekly"})

    def _build_mastery_card(self) -> ft.Control:
        theme = self.theme
        engine = self.state.lesson_engine
        completion = engine.category_completion(self.state.progress.get_completed_lesson_ids())

        self.mastery_bars: dict[str, ft.ProgressBar] = {}
        self.mastery_texts: dict[str, ft.Text] = {}
        category_rows: list[ft.Control] = []
        for category, (done, total) in completion.items():
            meta = get_category_meta(category)
            ratio = done / total if total else 0.0
            count_text = ft.Text(f"{done}/{total}", size=self._fs(13), color=theme.text_muted)
            bar = ft.ProgressBar(value=ratio, color=meta.color, bgcolor=theme.bg, height=8, border_radius=4)
            self.mastery_texts[category] = count_text
            self.mastery_bars[category] = bar
            category_rows.append(
                ft.Column(
                    [
                        ft.Row([ft.Text(f"{meta.icon} {meta.title}", size=self._fs(13), color=theme.text, width=200), count_text]),
                        bar,
                    ],
                    spacing=4,
                )
            )

        # Not a nested-scrollable Column (no scroll=AUTO, no fixed height) --
        # a scrollable inside a fixed-height box only ever showed a few rows
        # before clipping, since touch scroll on Android doesn't reliably
        # hand off between nested scroll regions. Letting this card grow to
        # its full natural height and scroll as part of the page's own
        # scroll (like every other card here) shows every category.
        return plain_card(
            theme,
            [self._card_title("📊 Category Mastery"), ft.Column(category_rows, spacing=12)],
            padding=20, width=_CARD_WIDTH, data={"kind": "parent_mastery"},
        )

    def _refresh_weekly_and_mastery(self) -> None:
        weekly = self.state.progress.get_weekly_summary()
        self.weekly_value_texts["lessons"].value = str(weekly.lessons_completed)
        self.weekly_value_texts["stars"].value = f"⭐ {weekly.stars_earned}"
        self.weekly_value_texts["quizzes"].value = str(weekly.quiz_attempts)
        self.weekly_value_texts["badges"].value = str(weekly.badges_earned)
        self.weekly_value_texts["active_days"].value = f"{weekly.active_days}/7"

        completion = self.state.lesson_engine.category_completion(self.state.progress.get_completed_lesson_ids())
        for category, (done, total) in completion.items():
            ratio = done / total if total else 0.0
            self.mastery_texts[category].value = f"{done}/{total}"
            self.mastery_bars[category].value = ratio

    def _refresh_activity(self) -> None:
        theme = self.theme
        recent = self.state.progress.get_recent_activity(limit=20)
        if not recent:
            self.activity_column.controls = [
                ft.Text(
                    "Nothing yet — activity shows up here once lessons begin.",
                    size=self._fs(13), color=theme.text_muted,
                )
            ]
        else:
            items: list[ft.Control] = []
            for row in recent:
                icon = EVENT_ICONS.get(row["event_type"], "•")
                label = EVENT_LABELS.get(row["event_type"], row["event_type"])
                lesson_part = f" ({row['lesson_id']})" if row["lesson_id"] else ""
                items.append(ft.Text(f"{icon} {label}{lesson_part}", size=self._fs(13), color=theme.text))
            self.activity_column.controls = items

    def _refresh_summary_values(self) -> None:
        fresh = self.state.progress.get_summary()
        player = self.state.progress.get_player_level()
        self.value_texts["level"].value = str(fresh.level)
        self.value_texts["player_level"].value = f"{player.level} · {level_title(player.level).title}"
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
        self._refresh_weekly_and_mastery()
        self._refresh_activity()
        self.status_text.value = "Progress has been reset."
        self.page.pop_dialog()
        self.page.update()

    def _on_menu(self, e) -> None:
        self.page.go("/hub")
