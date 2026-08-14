"""Entry point for the in-progress Flet re-platform (Windows + Android).

Separate from main.py (the CustomTkinter app your child actually uses
today) so this work-in-progress build never interferes with it -- see the
re-platform plan for the phased cutover. Run with:

    flet run main_flet.py
"""
from __future__ import annotations

import flet as ft

from app.ui.app_window_flet import main

ft.run(main)
