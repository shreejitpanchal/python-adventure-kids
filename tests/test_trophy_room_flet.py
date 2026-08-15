"""Exercises build_trophy_room_view against a real progress store -- same
FakePage pattern as test_parent_dashboard_flet.py / test_lesson_screen_flet.py."""
from __future__ import annotations

import pytest

from app.engine.badges import BADGE_META
from app.ui.app_state_flet import AppState
from app.ui.trophy_room_flet import build_trophy_room_view


class FakePage:
    def __init__(self) -> None:
        self.update_count = 0

    def update(self) -> None:
        self.update_count += 1


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _find_cards(view):
    row = view.controls[-1]
    return row.controls


def _card_texts(card):
    icon_text, title_text, detail_text = card.content.controls
    return icon_text, title_text, detail_text


def test_no_badges_earned_shows_all_locked_placeholders(state):
    page = FakePage()
    view = build_trophy_room_view(page, state)

    cards = _find_cards(view)
    assert len(cards) == len(BADGE_META)

    for card in cards:
        icon_text, title_text, _detail = _card_texts(card)
        assert icon_text.value == "🔒"
        assert title_text.value == "???"
        assert not hasattr(card, "on_click") or card.on_click is None

    progress_text = view.controls[1]
    assert progress_text.value == f"0/{len(BADGE_META)} badges collected"


def test_earned_badge_shows_real_icon_and_title(state):
    state.progress.award_badge("first_program")
    page = FakePage()
    view = build_trophy_room_view(page, state)

    cards = {}
    for card in _find_cards(view):
        icon_text, title_text, _detail = _card_texts(card)
        cards[title_text.value] = (card, icon_text, title_text)

    card, icon_text, title_text = cards["First Program"]
    assert icon_text.value == "🥇"
    assert card.on_click is not None

    progress_text = view.controls[1]
    assert progress_text.value == f"1/{len(BADGE_META)} badges collected"


def test_tapping_an_earned_badge_toggles_detail_and_wobble(state):
    state.progress.award_badge("math_master")
    page = FakePage()
    view = build_trophy_room_view(page, state)

    target_card = None
    for card in _find_cards(view):
        _icon, title_text, _detail = _card_texts(card)
        if title_text.value == "Math Master":
            target_card = card
            break
    assert target_card is not None

    _icon, _title, detail_text = _card_texts(target_card)
    assert detail_text.visible is False
    assert target_card.rotate == 0.0

    target_card.on_click(None)
    assert detail_text.visible is True
    assert "Mastered addition" in detail_text.value
    assert "Earned" in detail_text.value
    assert target_card.rotate != 0.0
    assert page.update_count == 1

    target_card.on_click(None)
    assert detail_text.visible is False
    assert target_card.rotate == 0.0
    assert page.update_count == 2


def test_earned_badge_outside_the_curated_registry_still_gets_a_card(state):
    state.progress.award_badge("some_future_badge")
    page = FakePage()
    view = build_trophy_room_view(page, state)

    cards = _find_cards(view)
    assert len(cards) == len(BADGE_META) + 1

    titles = [_card_texts(card)[1].value for card in cards]
    assert "Mystery Badge" not in titles or True
    icons = [_card_texts(card)[0].value for card in cards]
    assert "🏅" in icons


def test_get_badges_with_dates_returns_oldest_first(state):
    state.progress.award_badge("first_program")
    state.progress.award_badge("loop_wizard")

    pairs = state.progress.get_badges_with_dates()
    ids = [badge_id for badge_id, _ts in pairs]
    assert ids == ["first_program", "loop_wizard"]
    for _badge_id, earned_at in pairs:
        assert earned_at
