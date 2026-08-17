"""Parent area: progress summary and basic controls.

Full detail (activity log, per-lesson drill-down, settings) lands in a later phase;
this gives parents a real, working entry point today.
"""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.ui import theme
from app.ui.scroll_utils import install_fast_mousewheel_scrolling

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


def open_parent_area(app) -> None:
    _open_parent_window(app)


def _open_parent_window(app) -> None:
    win = ctk.CTkToplevel(app)
    win.title("Parent Area")
    win.geometry("480x600")
    win.minsize(360, 320)
    win.configure(fg_color=theme.COLOR_BG)
    win.transient(app)
    win.grab_set()

    body = ctk.CTkScrollableFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True)

    ctk.CTkLabel(
        body, text="👋 Parent Area", font=theme.font_heading(24), text_color=theme.COLOR_TEXT,
    ).pack(pady=(24, 16))

    summary = app.progress.get_summary()
    child_name = app.settings.child_name or "Your child"

    card = ctk.CTkFrame(body, fg_color=theme.COLOR_CARD, corner_radius=16)
    card.pack(fill="x", padx=24, pady=8)

    value_labels: dict[str, ctk.CTkLabel] = {}
    rows = [
        ("child", "Child", child_name),
        ("level", "Current level", str(summary.level)),
        ("stars", "Total stars", f"⭐ {summary.total_stars}"),
        ("lessons", "Lessons completed", str(summary.lessons_completed)),
        ("badges", "Badges earned", str(summary.badges_earned)),
        ("streak", "Day streak", str(summary.streak_days)),
    ]
    for key, label, value in rows:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row, text=label, font=theme.font_body(15), text_color=theme.COLOR_TEXT_MUTED).pack(side="left")
        value_label = ctk.CTkLabel(row, text=value, font=theme.font_body(15), text_color=theme.COLOR_TEXT)
        value_label.pack(side="right")
        value_labels[key] = value_label

    rename_card = ctk.CTkFrame(body, fg_color=theme.COLOR_CARD, corner_radius=16)
    rename_card.pack(fill="x", padx=24, pady=8)

    ctk.CTkLabel(
        rename_card, text="✏️ Child's Name", font=theme.font_heading(16), text_color=theme.COLOR_TEXT,
    ).pack(anchor="w", padx=20, pady=(16, 4))

    rename_row = ctk.CTkFrame(rename_card, fg_color="transparent")
    rename_row.pack(fill="x", padx=20, pady=(0, 16))

    name_entry = ctk.CTkEntry(rename_row, font=theme.font_body(15), height=36)
    name_entry.insert(0, app.settings.child_name)
    name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def save_name() -> None:
        new_name = name_entry.get().strip()
        if not new_name:
            return
        app.settings.child_name = new_name
        app.save_settings()
        value_labels["child"].configure(text=new_name)
        status_label.configure(text="Name updated.")

    name_entry.bind("<Return>", lambda _e: save_name())

    ctk.CTkButton(
        rename_row, text="Save", font=theme.font_body(13), width=80, height=36,
        fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
        command=save_name,
    ).pack(side="right")

    weekly_card = ctk.CTkFrame(body, fg_color=theme.COLOR_CARD, corner_radius=16)
    weekly_card.pack(fill="x", padx=24, pady=8)

    ctk.CTkLabel(
        weekly_card, text="📅 This Week", font=theme.font_heading(16), text_color=theme.COLOR_TEXT,
    ).pack(anchor="w", padx=20, pady=(16, 4))

    weekly_value_labels: dict[str, ctk.CTkLabel] = {}

    def _weekly_rows(summary):
        return [
            ("lessons", "Lessons completed", str(summary.lessons_completed)),
            ("stars", "Stars earned", f"⭐ {summary.stars_earned}"),
            ("quizzes", "Quiz attempts", str(summary.quiz_attempts)),
            ("badges", "Badges earned", str(summary.badges_earned)),
            ("active_days", "Active days", f"{summary.active_days}/7"),
        ]

    for key, label, value in _weekly_rows(app.progress.get_weekly_summary()):
        row = ctk.CTkFrame(weekly_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(row, text=label, font=theme.font_body(15), text_color=theme.COLOR_TEXT_MUTED).pack(side="left")
        value_label = ctk.CTkLabel(row, text=value, font=theme.font_body(15), text_color=theme.COLOR_TEXT)
        value_label.pack(side="right")
        weekly_value_labels[key] = value_label
    ctk.CTkFrame(weekly_card, fg_color="transparent", height=8).pack()

    def refresh_weekly() -> None:
        fresh = app.progress.get_weekly_summary()
        for key, _label, value in _weekly_rows(fresh):
            weekly_value_labels[key].configure(text=value)

    mastery_card = ctk.CTkScrollableFrame(body, fg_color=theme.COLOR_CARD, corner_radius=16, height=220)
    mastery_card.pack(fill="x", padx=24, pady=8)

    ctk.CTkLabel(
        mastery_card, text="📊 Category Mastery", font=theme.font_heading(16), text_color=theme.COLOR_TEXT,
    ).pack(anchor="w", padx=8, pady=(4, 8))

    mastery_labels: dict[str, ctk.CTkLabel] = {}
    mastery_bars: dict[str, ctk.CTkProgressBar] = {}

    def _build_mastery_rows() -> None:
        # Built once; reset updates these rows' labels/bars in place via
        # refresh_mastery() rather than rebuilding, since the set of
        # categories never changes within a single running session.
        completion = app.lesson_engine.category_completion(app.progress.get_completed_lesson_ids())
        for category, (done, total) in completion.items():
            meta = get_category_meta(category)
            row = ctk.CTkFrame(mastery_card, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=6)
            header = ctk.CTkFrame(row, fg_color="transparent")
            header.pack(fill="x")
            ctk.CTkLabel(
                header, text=f"{meta.icon} {meta.title}", font=theme.font_body(13), text_color=theme.COLOR_TEXT,
            ).pack(side="left")
            count_label = ctk.CTkLabel(
                header, text=f"{done}/{total}", font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
            )
            count_label.pack(side="right")
            bar = ctk.CTkProgressBar(row, progress_color=meta.color, height=8)
            bar.pack(fill="x", pady=(4, 0))
            bar.set(done / total if total else 0.0)
            mastery_labels[category] = count_label
            mastery_bars[category] = bar

    _build_mastery_rows()

    def refresh_mastery() -> None:
        completion = app.lesson_engine.category_completion(app.progress.get_completed_lesson_ids())
        for category, (done, total) in completion.items():
            if category in mastery_labels:
                mastery_labels[category].configure(text=f"{done}/{total}")
                mastery_bars[category].set(done / total if total else 0.0)

    ctk.CTkLabel(
        body, text="Recent Activity", font=theme.font_heading(16), text_color=theme.COLOR_TEXT,
    ).pack(anchor="w", padx=24, pady=(16, 4))

    activity_frame = ctk.CTkScrollableFrame(body, fg_color=theme.COLOR_CARD, corner_radius=16, height=160)
    activity_frame.pack(fill="x", padx=24, pady=(0, 8))

    def refresh_activity() -> None:
        for child in activity_frame.winfo_children():
            child.destroy()
        recent = app.progress.get_recent_activity(limit=20)
        if not recent:
            ctk.CTkLabel(
                activity_frame, text="Nothing yet — activity shows up here once lessons begin.",
                font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
            ).pack(anchor="w", padx=8, pady=8)
        else:
            for row in recent:
                icon = EVENT_ICONS.get(row["event_type"], "•")
                label = EVENT_LABELS.get(row["event_type"], row["event_type"])
                lesson_part = f" ({row['lesson_id']})" if row["lesson_id"] else ""
                ctk.CTkLabel(
                    activity_frame, text=f"{icon} {label}{lesson_part}", font=theme.font_body(13),
                    text_color=theme.COLOR_TEXT, anchor="w",
                ).pack(fill="x", padx=8, pady=2)

    refresh_activity()

    def refresh_summary() -> None:
        fresh = app.progress.get_summary()
        value_labels["level"].configure(text=str(fresh.level))
        value_labels["stars"].configure(text=f"⭐ {fresh.total_stars}")
        value_labels["lessons"].configure(text=str(fresh.lessons_completed))
        value_labels["badges"].configure(text=str(fresh.badges_earned))
        value_labels["streak"].configure(text=str(fresh.streak_days))

    status_label = ctk.CTkLabel(body, text="", font=theme.font_body(13), text_color=theme.COLOR_SUCCESS)
    status_label.pack(pady=(12, 0))

    progress_changed = False

    def close_window() -> None:
        if progress_changed:
            app.show_hub()
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", close_window)

    def confirm_reset() -> None:
        confirm = ctk.CTkToplevel(win)
        confirm.title("Reset progress?")
        confirm.geometry("360x180")
        confirm.configure(fg_color=theme.COLOR_BG)
        confirm.transient(win)
        confirm.grab_set()

        ctk.CTkLabel(
            confirm, text=f"Reset all of {app.settings.child_name or 'Your child'}'s progress?\nThis can't be undone.",
            font=theme.font_body(14), text_color=theme.COLOR_TEXT, justify="center",
        ).pack(pady=(24, 16))

        btn_row = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_row.pack()

        def do_reset() -> None:
            nonlocal progress_changed
            app.progress.reset_progress()
            progress_changed = True
            refresh_summary()
            refresh_weekly()
            refresh_mastery()
            refresh_activity()
            confirm.destroy()
            status_label.configure(text="Progress has been reset.")

        ctk.CTkButton(
            btn_row, text="Cancel", width=120, fg_color=theme.COLOR_TEXT_MUTED,
            command=confirm.destroy,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="Reset", width=120, fg_color=theme.COLOR_DANGER,
            hover_color="#D94F4F", command=do_reset,
        ).pack(side="left", padx=8)

    ctk.CTkButton(
        body, text="Reset Progress", font=theme.font_body(14), width=200, height=40,
        fg_color=theme.COLOR_DANGER, hover_color="#D94F4F",
        command=confirm_reset,
    ).pack(pady=(20, 8))

    ctk.CTkButton(
        body, text="Close", font=theme.font_body(14), width=200, height=40,
        fg_color=theme.COLOR_TEXT_MUTED,
        command=close_window,
    ).pack(pady=(4, 24))

    install_fast_mousewheel_scrolling(win)
