import pytest

from app.engine.outfits import OUTFITS
from app.ui.app_state_flet import AppState
from app.ui.codey_closet_flet import build_closet_view, closet_line
from tests.flet_testing import FakePage, all_of, one


class ViewsPage(FakePage):
    def __init__(self) -> None:
        super().__init__()
        self.views: list = []


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _tile(view, outfit_id):
    return next(t for t in all_of(view, "outfit_tile") if t.data["id"] == outfit_id)


def _button(tile):
    return tile.content.controls[-1]


def test_fresh_closet_shows_every_outfit_locked_and_just_codey_worn(state):
    view = build_closet_view(FakePage(), state)
    assert one(view, "star_balance").data["label"] == "0 stars to spend"
    tiles = all_of(view, "outfit_tile")
    assert len(tiles) == len(OUTFITS) + 1
    assert _tile(view, None).data["equipped"] is True
    for outfit in OUTFITS:
        tile = _tile(view, outfit.id)
        assert tile.data == {"kind": "outfit_tile", "id": outfit.id, "owned": False, "equipped": False, "affordable": False}
        assert _button(tile).disabled is True


def test_buying_spends_stars_equips_and_rebuilds(state):
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.complete_lesson("lesson_02", 3)
    state.progress.complete_lesson("lesson_03", 3)
    state.progress.complete_lesson("lesson_04", 3)  # 12 stars
    page = ViewsPage()
    view = build_closet_view(page, state)
    glasses = _tile(view, "glasses")
    assert glasses.data["affordable"] is True and glasses.data["owned"] is False

    _button(glasses).on_click(None)

    assert state.progress.get_star_balance() == 2
    assert state.progress.get_equipped_outfit() == "glasses"
    assert len(page.views) == 1, "the view was rebuilt in place"
    rebuilt = page.views[0]
    assert _tile(rebuilt, "glasses").data["equipped"] is True
    assert one(rebuilt, "star_balance").data["label"] == "2 stars to spend"
    assert one(rebuilt, "codey_accessory").data["accessory"] == "👓"


def test_wearing_and_taking_off_owned_outfits(state):
    for lesson_id in ("lesson_01", "lesson_02", "lesson_03", "lesson_04"):
        state.progress.complete_lesson(lesson_id, 3)
    assert state.progress.buy_outfit("glasses", 10)
    state.progress.equip_outfit(None)
    page = ViewsPage()
    view = build_closet_view(page, state)
    glasses = _tile(view, "glasses")
    assert glasses.data["owned"] is True and glasses.data["equipped"] is False

    _button(glasses).on_click(None)
    assert state.progress.get_equipped_outfit() == "glasses"

    none_tile = _tile(page.views[-1], None)
    _button(none_tile).on_click(None)
    assert state.progress.get_equipped_outfit() is None


def test_closet_line():
    assert "Earn stars" in closet_line(0, 0, 9)
    assert "12 stars" in closet_line(12, 1, 9)
    assert "every outfit" in closet_line(0, 9, 9)
