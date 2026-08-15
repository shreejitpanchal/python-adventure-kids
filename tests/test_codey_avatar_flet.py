from app.ui.components.codey_avatar_flet import CodeyState, build_codey_avatar
from app.ui.theme_flet import get_preset


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
