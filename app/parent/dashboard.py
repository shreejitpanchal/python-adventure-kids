"""PIN-gated parent area: progress summary and basic controls.

Full detail (activity log, per-lesson drill-down, settings) lands in a later phase;
this gives parents a real, working entry point today.
"""
from __future__ import annotations

import customtkinter as ctk

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
    if app.settings.has_parent_pin():
        _open_pin_prompt(app)
    else:
        _open_parent_window(app)


def _open_pin_prompt(app) -> None:
    dialog = ctk.CTkToplevel(app)
    dialog.title("Parent Area")
    dialog.geometry("360x260")
    dialog.configure(fg_color=theme.COLOR_BG)
    dialog.transient(app)
    dialog.grab_set()

    ctk.CTkLabel(
        dialog, text="🔒 Parent Area", font=theme.font_heading(22), text_color=theme.COLOR_TEXT,
    ).pack(pady=(30, 10))

    ctk.CTkLabel(
        dialog, text="Enter the 4-digit PIN", font=theme.font_body(14),
        text_color=theme.COLOR_TEXT_MUTED,
    ).pack(pady=(0, 10))

    pin_entry = ctk.CTkEntry(
        dialog, font=theme.font_body(22), width=160, height=44,
        justify="center", show="•",
    )
    pin_entry.pack()
    pin_entry.focus_set()

    error_label = ctk.CTkLabel(dialog, text="", font=theme.font_body(13), text_color=theme.COLOR_DANGER)
    error_label.pack(pady=8)

    def submit(_event=None) -> None:
        if app.settings.verify_parent_pin(pin_entry.get().strip()):
            dialog.destroy()
            _open_parent_window(app)
        else:
            error_label.configure(text="Incorrect PIN.")
            pin_entry.delete(0, "end")

    pin_entry.bind("<Return>", submit)

    ctk.CTkButton(
        dialog, text="Unlock", font=theme.font_button(16), width=140, height=40,
        fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
        command=submit,
    ).pack(pady=10)


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

    if not app.settings.has_parent_pin():
        ctk.CTkLabel(
            body, text="No PIN is set yet — anyone can open this area.",
            font=theme.font_body(13), text_color=theme.COLOR_WARNING,
        ).pack(pady=(16, 0))

    status_label = ctk.CTkLabel(body, text="", font=theme.font_body(13), text_color=theme.COLOR_SUCCESS)
    status_label.pack(pady=(12, 0))

    progress_changed = False

    def close_window() -> None:
        if progress_changed:
            app.show_dashboard()
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
            confirm, text=f"Reset all of {child_name}'s progress?\nThis can't be undone.",
            font=theme.font_body(14), text_color=theme.COLOR_TEXT, justify="center",
        ).pack(pady=(24, 16))

        btn_row = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_row.pack()

        def do_reset() -> None:
            nonlocal progress_changed
            app.progress.reset_progress()
            progress_changed = True
            refresh_summary()
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
