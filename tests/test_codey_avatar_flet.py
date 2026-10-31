from app.ui.components import motion_flet as motion
from app.ui.components.codey_avatar_flet import CodeyState, build_codey_avatar, build_codey_companion
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, NoTaskPage, one


def test_starts_in_the_idle_state():
    handle = build_codey_avatar(get_preset("midnight_dark"))
    assert handle.face_text.value == "🤖"
    assert handle.caption_text.value == "Ready when you are!"


def test_set_state_updates_face_and_caption_for_every_known_state():
    handle = build_codey_avatar(get_preset("midnight_dark"))
    seen_faces = set()
    seen_captions = set()

    for state in (
        CodeyState.IDLE, CodeyState.RUNNING, CodeyState.SUCCESS,
        CodeyState.WARNING, CodeyState.ERROR, CodeyState.BLOCKED,
    ):
        handle.set_state(state)
        assert handle.face_text.value
        assert handle.caption_text.value
        seen_faces.add(handle.face_text.value)
        seen_captions.add(handle.caption_text.value)

    assert len(seen_faces) == 6, "every state should have a visually distinct face"
    assert len(seen_captions) == 6, "every state should have a distinct caption"


def test_unknown_state_falls_back_to_idle():
    handle = build_codey_avatar(get_preset("midnight_dark"))
    handle.set_state(CodeyState.SUCCESS)
    assert handle.face_text.value != "🤖"

    handle.set_state("not-a-real-state")
    assert handle.face_text.value == "🤖"
    assert handle.caption_text.value == "Ready when you are!"


def test_control_is_built_and_contains_the_live_text_controls():
    handle = build_codey_avatar(get_preset("sunny_light"))
    # face_text/caption_text must be the actual controls rendered inside
    # .control, not disconnected copies -- otherwise set_state() wouldn't
    # visibly update anything.
    handle.set_state(CodeyState.SUCCESS)

    def contains(control, target) -> bool:
        if control is target:
            return True
        children = getattr(control, "controls", None) or ([control.content] if getattr(control, "content", None) else [])
        return any(contains(c, target) for c in children if c is not None)

    assert contains(handle.control, handle.face_text)
    assert contains(handle.control, handle.caption_text)


# -- the companion (Hub / Dashboard / Map) --------------------------------------
def test_companion_shows_its_line_and_can_change_it():
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "Hello there!")
    assert one(handle.control, "codey_companion") is handle.control
    assert handle.line_text.value == "Hello there!"
    assert handle.face_text.value == "🤖"
    handle.set_line("New line")
    assert handle.line_text.value == "New line"


def test_companion_floats_only_when_given_a_page():
    page = FakePage()
    build_codey_companion(get_preset("sunny_light"), 1.0, "hi", page=page)
    assert len(page.scheduled(motion._bob)) == 1

    quiet = FakePage()
    build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    assert quiet.run_task_calls == []


def test_companion_accessory_badge_is_hidden_without_one_and_shown_with_one():
    plain = build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    badge = one(plain.control, "codey_accessory")
    assert badge.visible is False and badge.data["accessory"] == ""

    crowned = build_codey_companion(get_preset("sunny_light"), 1.0, "hi", accessory="👑")
    badge = one(crowned.control, "codey_accessory")
    assert badge.visible is True and badge.content.value == "👑"


def test_companion_cheer_switches_face_and_pulses():
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    page = FakePage()
    assert handle.cheer(page) is True
    assert handle.face_text.value == "🎉"
    assert len(page.scheduled(motion._pulse)) == 1
    assert handle.cheer(NoTaskPage()) is False


# -- idle life + tap to wave ------------------------------------------------------------
def test_companion_with_a_page_idles_and_is_tappable():
    from app.ui.components import codey_avatar_flet as codey

    page = FakePage()
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "hi", page=page)
    assert len(page.scheduled(codey._idle)) == 1
    assert handle.inner_disc is one(handle.control, "codey_disc")
    assert handle.inner_disc.on_click is not None and handle.inner_disc.ink is True
    assert handle.inner_disc.scale.scale_y == 1.0, "blink tween armed"

    static = build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    assert static.inner_disc.on_click is None


def test_idle_loop_blinks_and_looks_around_then_rests(monkeypatch):
    import asyncio

    from app.ui.components import codey_avatar_flet as codey

    async def no_sleep(_s):
        return None

    from app.ui.components import codey_face_flet as face_module

    monkeypatch.setattr(codey.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(motion.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(face_module.asyncio, "sleep", no_sleep)
    page = FakePage()
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "hi", page=page)
    ((args, _k),) = page.scheduled(codey._idle)
    asyncio.run(codey._idle(*args))
    disc = handle.inner_disc
    assert disc.rotate == 0.0 and disc.scale.scale_y == 1.0
    assert page.update_count == codey.IDLE_CYCLES * 2 + (codey.IDLE_CYCLES // 2) * 3


def test_wave_says_hello_wobbles_and_schedules_the_swap_back(monkeypatch):
    import asyncio

    from app.ui.components import codey_avatar_flet as codey

    async def no_sleep(_s):
        return None

    monkeypatch.setattr(codey.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(motion.asyncio, "sleep", no_sleep)
    page = FakePage()
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "Original line", page=page)

    assert handle.wave(page) is True
    assert handle.face_text.value == codey.WAVE_FACE
    assert handle.line_text.value == codey.WAVE_LINES[0]
    assert handle.wave(page) is False, "no stacked waves while one is playing"

    ((args, _k),) = page.scheduled(codey._wave)
    asyncio.run(codey._wave(*args))
    assert handle.face_text.value == "🤖" and handle.line_text.value == "Original line"
    assert handle.inner_disc.rotate == 0.0

    # A second wave later cycles to the next line.
    handle.wave(page)
    assert handle.line_text.value == codey.WAVE_LINES[1]

    # Without a schedulable page the hello simply stays.
    quiet = build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    assert quiet.wave(NoTaskPage()) is False
    assert quiet.face_text.value == codey.WAVE_FACE


def test_drawn_face_mirrors_the_semantic_face_and_badges_non_robot_emoji():
    handle = build_codey_companion(get_preset("sunny_light"), 1.0, "hi")
    assert handle.face.expression == "idle"
    assert handle.face_text.visible is False, "the plain robot is drawn, not shown as emoji"

    handle.cheer(FakePage())
    assert handle.face_text.value == "🎉" and handle.face_text.visible is True
    assert handle.face.expression == "happy"

    avatar = build_codey_avatar(get_preset("sunny_light"))
    avatar.set_state(CodeyState.ERROR)
    assert avatar.face.expression == "dizzy" and avatar.face_text.visible is True
    avatar.set_state(CodeyState.IDLE)
    assert avatar.face.expression == "idle" and avatar.face_text.visible is False
    avatar.show_face("🎲")
    assert avatar.face_text.value == "🎲" and avatar.face.expression == "surprised"


def test_lesson_avatar_idles_only_when_given_a_page():
    from app.ui.components import codey_avatar_flet as codey

    page = FakePage()
    build_codey_avatar(get_preset("sunny_light"), page=page)
    assert len(page.scheduled(codey._idle)) == 1
    quiet = FakePage()
    build_codey_avatar(get_preset("sunny_light"))
    assert quiet.run_task_calls == []
