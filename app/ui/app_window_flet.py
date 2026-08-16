"""Root Flet application: route-based navigation between full-screen views.

The Flet analogue of app/ui/app_window.py's show_frame() destroy/recreate
pattern -- here it's page.views.clear() + page.views.append(...) on every
route change, which is Flet's own idiomatic navigation model and also
gives correct Android back-button behavior for free.
"""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.category_levels_flet import build_category_levels_view
from app.ui.category_map_flet import build_category_map_view
from app.ui.dashboard_flet import build_dashboard_view
from app.ui.journey_map_flet import build_journey_map_view
from app.ui.lesson_screen_flet import build_lesson_view
from app.ui.module_detail_flet import build_module_detail_view
from app.ui.parent_dashboard_flet import build_parent_view
from app.ui.quiz_screen_flet import build_quiz_view
from app.ui.settings_screen_flet import build_settings_view
from app.ui.setup_wizard_flet import build_setup_wizard_view
from app.ui.trophy_room_flet import build_trophy_room_view


def main(page: ft.Page) -> None:
    page.title = "Python Adventure"
    page.window.width = 1000
    page.window.height = 700
    page.window.icon = "main-icon.png"
    page.padding = 0
    page.fonts = {"Baloo 2": "fonts/Baloo2-Regular.ttf"}
    page.theme = ft.Theme(font_family="Baloo 2")
    page.dark_theme = ft.Theme(font_family="Baloo 2")

    state = AppState()
    # state.sound_player stays None (its default -- see AppState.__init__)
    # rather than constructing SoundPlayerFlet(page) here: flet_audio's
    # Audio control needs its Flutter/Dart implementation compiled into
    # the connected client to render at all. The generic "Flet" companion
    # app used for `flet run` live-preview on a real device only knows
    # Flet's built-in controls -- any extension control (this one
    # included) shows a client-side "Unknown control: Audio" red banner
    # that no Python-side fix can suppress, confirmed via real-device
    # testing. Re-enabling this needs verifying flet-audio's Flutter
    # package actually gets bundled into a real `flet build apk` output
    # (not just the live-preview client) before it's safe to turn back on
    # -- every other sound-related piece (app/audio/player.py's shared
    # decision logic, CTk's winsound-based playback, SoundPlayerFlet
    # itself, the Settings toggle) is untouched and ready to re-wire with
    # a one-line change once that's confirmed.

    def route_change(_e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        route = page.route

        if route.startswith("/categories/"):
            category = route.removeprefix("/categories/")
            page.views.append(build_category_levels_view(page, state, category))
        elif route == "/categories":
            page.views.append(build_category_map_view(page, state))
        elif route.startswith("/journey/"):
            module_id = route.removeprefix("/journey/")
            page.views.append(build_module_detail_view(page, state, module_id))
        elif route == "/journey":
            page.views.append(build_journey_map_view(page, state))
        elif route == "/settings":
            page.views.append(build_settings_view(page, state))
        elif route == "/parent":
            page.views.append(build_parent_view(page, state))
        elif route == "/quiz":
            page.views.append(build_quiz_view(page, state))
        elif route == "/trophy-room":
            page.views.append(build_trophy_room_view(page, state))
        elif route.startswith("/lesson/"):
            lesson_id = route.removeprefix("/lesson/")
            page.views.append(build_lesson_view(page, state, lesson_id))
        elif route == "/setup":
            page.views.append(build_setup_wizard_view(page, state))
        else:
            state.progress.record_play_today()
            page.views.append(build_dashboard_view(page, state))

        page.bgcolor = state.theme.bg
        page.theme_mode = ft.ThemeMode.DARK if state.theme.is_dark else ft.ThemeMode.LIGHT
        page.update()

    def view_pop(_e: ft.ViewPopEvent) -> None:
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/setup" if not state.settings.setup_complete else "/dashboard")
