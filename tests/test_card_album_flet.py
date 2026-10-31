"""The Card Album screen against a real AppState: one tile per concept
tag, collected ones face up and tappable."""
from __future__ import annotations

import pytest

from app.engine.cards import all_cards
from app.ui.app_state_flet import AppState
from app.ui.card_album_flet import build_card_album_view, codey_album_line
from tests.flet_testing import FakePage, all_of, one, texts


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def test_fresh_album_shows_every_card_face_down(state):
    view = build_card_album_view(FakePage(), state, hour=12)
    tiles = all_of(view, "concept_card")
    assert len(tiles) == len(all_cards(state.lesson_engine, []))
    assert all(not tile.data["collected"] and tile.on_click is None for tile in tiles)
    assert one(view, "album_progress").data == {"kind": "album_progress", "collected": 0, "total": len(tiles)}
    assert view.bottom_appbar.data["active"] == "trophies"
    assert one(view, "sky_backdrop").data["moment"] == "day"
    assert "???" in texts(view)


def test_completing_a_lesson_flips_its_cards_and_they_toggle_their_blurb(state):
    state.progress.complete_lesson("lesson_01", 3)
    page = FakePage()
    view = build_card_album_view(page, state)
    lesson = state.lesson_engine.get("lesson_01")
    collected = [tile for tile in all_of(view, "concept_card") if tile.data["collected"]]
    assert {tile.data["tag"] for tile in collected} == set(lesson.concept_tags)
    assert all(tile.data["level"] == 1 and tile.on_click is not None for tile in collected)

    tile = collected[0]
    blurb = tile.content.content.controls[-1]
    assert blurb.visible is False
    tile.on_click(None)
    assert blurb.visible is True and page.update_count >= 1


def test_codey_album_line():
    assert "first concept card" in codey_album_line(0, 5)
    assert codey_album_line(0, 0) == "No cards in this curriculum yet."
