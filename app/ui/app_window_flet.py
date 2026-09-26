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

import os

import flet as ft

from app.engine.categories import PROJECT_CATEGORIES
from app.engine.courses import AI_ML_COURSE
from app.ui.app_state_flet import AppState
from app.ui.components.adventure_kit_flet import layout_for
from app.ui.components.sound_player_flet import SoundPlayerFlet
from app.ui.category_levels_flet import build_category_levels_view
from app.ui.category_map_flet import build_category_map_view
from app.ui.codey_closet_flet import build_closet_view
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


SOUND_ENV_VAR = "PYADV_SOUND"


def sound_wiring_enabled() -> bool:
    """True only when PYADV_SOUND is set to 1/true/on/yes. Opt-in, not
    default: a real `flet build apk` install (2026-09-27, Android) still
    rendered a full-height red "Unknown control: Audio" strip, i.e. the
    flet_audio Flutter package was not in the built client either -- not
    just the live-preview one. Until a build is confirmed to bundle it
    (see docs/DEVELOPMENT.md "Sound on Flet"), the Audio controls must not
    be created at all."""
    return os.environ.get(SOUND_ENV_VAR, "0").strip().lower() in ("1", "true", "on", "yes")


def main(page: ft.Page) -> None:
    page.title = "Python Adventure"
    page.window.width = 1000
    page.window.height = 700
    page.window.icon = "main-icon.png"
    page.padding = 0
    page.fonts = {"Baloo 2": "fonts/Baloo2-Regular.ttf"}

    state = AppState()
    # Advance the day streak the moment the app opens -- the Hub is the
    # landing screen and shows the streak/welcome-back moment, so waiting
    # for a Dashboard visit (which also calls this, idempotently) would
    # leave the Hub a day behind. See AppState.welcome.
    state.welcome = state.progress.record_play_today()
    # Chimes (app/ui/components/sound_player_flet.py). flet_audio's Audio
    # control only renders in a client that has its Flutter package
    # compiled in; otherwise the client paints a red "Unknown control:
    # Audio" strip over the whole app. That happened in a real APK build,
    # so the wiring is opt-in (PYADV_SOUND=1) until a build is shown to
    # bundle the package -- see sound_wiring_enabled(). The Settings toggle
    # (Settings.sound_enabled) is the child's own control on top of that.
    if sound_wiring_enabled():
        state.sound_player = SoundPlayerFlet(page)

    # Unlike sound_player, there's no state.file_picker built here: an
    # earlier version of this code built one ft.FilePicker up front and
    # added it to page.overlay -- the pattern SoundPlayerFlet uses for its
    # Audio controls (see that class) -- which rendered as an "Unknown
    # control: FilePicker" error on Android. The actual cause turned out to
    # be different from sound_player's real limitation above: ft.FilePicker
    # (and ft.Share) are Service controls, which self-register with
    # whichever page is current via Service.init()'s
    # context.page._services.register_service() the moment they're
    # constructed inside a running page session -- page.overlay is a
    # different, older registration path meant for visual overlay controls
    # (like SnackBar), not Service controls. settings_screen_flet.py's
    # export/import handlers construct a fresh ft.FilePicker()/ft.Share()
    # inline instead, which registers correctly.

    # Python-side back-navigation stack -- see module docstring. Holds
    # previous routes, most recent last; "/setup" is never pushed since
    # it's a one-time onboarding flow, not a screen to return to.
    history: list[str] = []
    navigating_back = {"value": False}
    # Set while route_change() re-runs for the *same* route because a
    # window resize crossed the compact/wide breakpoint (see on_resized
    # below) -- a rebuild, not a navigation, so it must not push history.
    rebuilding = {"value": False}
    layout_class = {"wide": None}

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

        if (
            not navigating_back["value"] and not rebuilding["value"]
            and page.views and page.views[-1].route != "/setup"
        ):
            history.append(page.views[-1].route)
        navigating_back["value"] = False
        rebuilding["value"] = False
        layout_class["wide"] = layout_for(page).wide

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
        elif route == "/closet":
            page.views.append(build_closet_view(page, state))
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

    def on_resized(_e) -> None:
        """Rebuilds the current view when a resize crosses the compact/wide
        breakpoint, so a desktop window and a phone get the layout that
        fits them (adventure_kit_flet.layout_for). Never on a lesson: the
        lesson screen is width-agnostic and a rebuild would throw away
        the child's typed code."""
        if not page.views or page.route.startswith("/lesson/"):
            return
        if layout_for(page).wide != layout_class["wide"]:
            rebuilding["value"] = True
            route_change(None)

    page.on_resized = on_resized

    page.go("/setup" if not state.settings.setup_complete else "/hub")
