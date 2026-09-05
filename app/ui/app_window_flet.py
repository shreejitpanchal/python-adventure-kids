"""Root Flet application: route-based navigation between full-screen views.

The Flet analogue of app/ui/app_window.py's show_frame() destroy/recreate
pattern -- page.views.clear() + page.views.append(...) on every route
change, rebuilding exactly one view fresh each time (cheap, and avoids
ever showing stale progress/XP numbers on a view built earlier).

Because page.views is deliberately kept at length 1, it can't double as
Flet's own back-navigation stack. `history` below is a small Python-side
stack of prior routes that stands in for that: every ordinary forward
navigation (any page.go(...) from a button, not a back step) pushes the
screen being left; at the true root (Hub, history empty) the back button
closes the app, matching normal Android behavior for a top-level screen.

Each View's `can_pop` defaults to True in this Flet version, which lets
Flutter's Navigator pop it immediately without ever asking Python first --
with only one view ever on the stack, a "successful" pop has nothing left
to reveal, so it just closes the app outright (confirmed via real-device
Android testing: the hardware back button always closed the app, never
returned to the previous screen, regardless of the `history` stack below).
Every view built here gets `can_pop=False` + `on_confirm_pop=confirm_pop`
instead, so Flutter asks Python before acting: confirm_pop() consults
`history` and either navigates to the previous route (canceling the actual
pop, since navigation happens via page.go() instead) or, when history is
empty, lets the pop proceed and the app close.
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import PROJECT_CATEGORIES
from app.engine.courses import AI_ML_COURSE
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

    # state.file_picker stays None (its default) for the exact same reason
    # sound_player does, confirmed via the same kind of real-device testing:
    # ft.FilePicker also renders as an "Unknown control: FilePicker" red
    # banner on the generic live-preview client -- and because
    # page.overlay controls are attached at startup regardless of route,
    # this one broke app launch entirely, not just the Settings screen.
    # Settings' Export/Import buttons already guard for file_picker being
    # None (see settings_screen_flet.py) and show a friendly message
    # instead of crashing. Re-enabling needs the same real `flet build apk`
    # confirmation flet_audio's Audio control is waiting on above.

    # Python-side back-navigation stack -- see module docstring. Holds
    # previous routes, most recent last; "/setup" is never pushed since
    # it's a one-time onboarding flow, not a screen to return to.
    history: list[str] = []
    navigating_back = {"value": False}

    async def confirm_pop(e: ft.ControlEvent) -> None:
        view = e.control
        if history:
            previous_route = history.pop()
            navigating_back["value"] = True
            await view.confirm_pop(False)
            page.go(previous_route)
        else:
            await view.confirm_pop(True)

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
        elif route == "/ai-course":
            page.views.append(build_course_map_view(page, state, course=AI_ML_COURSE))
        elif route.startswith("/ai-course-quiz/"):
            lesson_id = route.removeprefix("/ai-course-quiz/")
            page.views.append(build_course_quiz_view(page, state, lesson_id, course=AI_ML_COURSE))
        elif route.startswith("/ai-course/"):
            category = route.removeprefix("/ai-course/")
            page.views.append(build_course_chapter_view(page, state, category, course=AI_ML_COURSE))
        elif route == "/trophy-room":
            page.views.append(build_trophy_room_view(page, state))
        elif route.startswith("/lesson/"):
            lesson_id = route.removeprefix("/lesson/")
            page.views.append(build_lesson_view(page, state, lesson_id))
        elif route == "/setup":
            page.views.append(build_setup_wizard_view(page, state))
        else:
            page.views.append(build_learning_hub_view(page, state))

        # can_pop=False makes Flutter ask confirm_pop() before acting on a
        # back-navigation attempt (hardware back button, included) instead
        # of popping (and, since this is the only view, closing the app)
        # immediately -- see module docstring for why can_pop's default of
        # True bypassed the `history` stack entirely.
        page.views[-1].can_pop = False
        page.views[-1].on_confirm_pop = confirm_pop

        page.bgcolor = state.theme.bg
        page.theme_mode = ft.ThemeMode.DARK if state.theme.is_dark else ft.ThemeMode.LIGHT
        page.theme = ft.Theme(font_family=state.font_family)
        page.dark_theme = ft.Theme(font_family=state.font_family)
        page.update()

    page.on_route_change = route_change

    page.go("/setup" if not state.settings.setup_complete else "/hub")
