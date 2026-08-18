"""Root Flet application: route-based navigation between full-screen views.

The Flet analogue of app/ui/app_window.py's show_frame() destroy/recreate
pattern -- page.views.clear() + page.views.append(...) on every route
change, rebuilding exactly one view fresh each time (cheap, and avoids
ever showing stale progress/XP numbers on a view built earlier).

Because page.views is deliberately kept at length 1, it can't double as
Flet's own back-navigation stack (Flet's on_view_pop pattern expects
page.views to hold real history to pop from -- with only ever one entry,
the system/hardware back button on Android had nothing to pop and closed
the app instead of returning to the previous screen). `history` below is
a small Python-side stack of prior routes that stands in for that: every
ordinary forward navigation (any page.go(...) from a button, not a back
step) pushes the screen being left; on_view_pop pops it and re-navigates
there; at the true root (Hub, history empty) the back button closes the
app, matching normal Android behavior for a top-level screen.
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import PROJECT_CATEGORIES
from app.ui.app_state_flet import AppState
from app.ui.category_levels_flet import build_category_levels_view
from app.ui.category_map_flet import build_category_map_view
from app.ui.course_chapter_flet import build_course_chapter_view
from app.ui.course_map_flet import build_course_map_view
from app.ui.course_quiz_screen_flet import build_course_quiz_view
from app.ui.dashboard_flet import build_dashboard_view
from app.ui.learning_hub_flet import build_learning_hub_view
from app.ui.lesson_screen_flet import build_lesson_view
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

    # Python-side back-navigation stack -- see module docstring. Holds
    # previous routes, most recent last; "/setup" is never pushed since
    # it's a one-time onboarding flow, not a screen to return to.
    history: list[str] = []
    navigating_back = {"value": False}

    def route_change(_e: ft.RouteChangeEvent) -> None:
        route = page.route

        if not navigating_back["value"] and page.views and page.views[-1].route != "/setup":
            history.append(page.views[-1].route)
        navigating_back["value"] = False

        page.views.clear()

        if route == "/hub":
            page.views.append(build_learning_hub_view(page, state))
        elif route == "/dashboard":
            state.progress.record_play_today()
            page.views.append(build_dashboard_view(page, state))
        elif route == "/projects":
            page.views.append(build_category_map_view(
                page, state, category_filter=PROJECT_CATEGORIES, heading="🛠️ Build a Project",
            ))
        elif route.startswith("/categories/"):
            category = route.removeprefix("/categories/")
            page.views.append(build_category_levels_view(page, state, category))
        elif route == "/categories":
            page.views.append(build_category_map_view(page, state))
        elif route == "/settings":
            page.views.append(build_settings_view(page, state))
        elif route == "/parent":
            page.views.append(build_parent_view(page, state))
        elif route == "/quiz":
            page.views.append(build_quiz_view(page, state))
        elif route == "/course":
            page.views.append(build_course_map_view(page, state))
        elif route.startswith("/course-quiz/"):
            lesson_id = route.removeprefix("/course-quiz/")
            page.views.append(build_course_quiz_view(page, state, lesson_id))
        elif route.startswith("/course/"):
            category = route.removeprefix("/course/")
            page.views.append(build_course_chapter_view(page, state, category))
        elif route == "/trophy-room":
            page.views.append(build_trophy_room_view(page, state))
        elif route.startswith("/lesson/"):
            lesson_id = route.removeprefix("/lesson/")
            page.views.append(build_lesson_view(page, state, lesson_id))
        elif route == "/setup":
            page.views.append(build_setup_wizard_view(page, state))
        else:
            page.views.append(build_learning_hub_view(page, state))

        page.bgcolor = state.theme.bg
        page.theme_mode = ft.ThemeMode.DARK if state.theme.is_dark else ft.ThemeMode.LIGHT
        page.theme = ft.Theme(font_family=state.font_family)
        page.dark_theme = ft.Theme(font_family=state.font_family)
        page.update()

    def view_pop(_e: ft.ViewPopEvent) -> None:
        if history:
            previous_route = history.pop()
            navigating_back["value"] = True
            page.go(previous_route)
        else:
            page.run_task(page.window.close)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/setup" if not state.settings.setup_complete else "/hub")
