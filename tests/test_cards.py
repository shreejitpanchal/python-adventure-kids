"""app/engine/cards.py: concept cards derived from completed lessons' tags,
against the real LessonEngine."""
from __future__ import annotations

import pytest

from app.engine.cards import (
    CARD_META, DEFAULT_CARD_COLOR, album_line, all_cards, card_meta, collected_cards, newly_collected_tags,
)
from app.engine.lesson_engine import LessonEngine


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_every_tag_in_the_curriculum_becomes_a_card_and_an_unknown_tag_still_renders(engine):
    cards = all_cards(engine, [])
    tags = {tag for lesson in engine.all_in_order() for tag in (lesson.concept_tags or [])}
    assert {card.tag for card in cards} == tags
    assert all(not card.collected for card in cards)
    assert cards[0].total >= cards[-1].total, "most common tags first"
    generic = card_meta("something-new")
    assert generic.title == "Something New" and generic.color == DEFAULT_CARD_COLOR
    assert all(meta.icon and meta.blurb for meta in CARD_META.values())


def test_completing_a_lesson_collects_its_tags_and_levels_them(engine):
    first = engine.get("lesson_01")
    assert first.concept_tags, "lesson_01 should carry concept tags"
    cards = {card.tag: card for card in collected_cards(engine, ["lesson_01"])}
    assert set(cards) == set(first.concept_tags)
    assert all(card.level == 1 and card.collected for card in cards.values())

    with_more = {card.tag: card for card in all_cards(engine, ["lesson_01", "lesson_02"])}
    shared = set(first.concept_tags) & set(engine.get("lesson_02").concept_tags)
    for tag in shared:
        assert with_more[tag].level == 2


def test_rarity_follows_how_many_lessons_teach_the_tag(engine):
    by_tag = {card.tag: card for card in all_cards(engine, [])}
    assert by_tag["errors"].rarity == "common"
    assert by_tag["random"].rarity == "legendary"
    rare = [card for card in by_tag.values() if card.rarity == "rare"]
    assert rare and all(3 < card.total <= 10 for card in rare)


def test_newly_collected_tags_reports_only_first_time_tags(engine):
    first = engine.get("lesson_01")
    assert newly_collected_tags(engine, first, []) == list(dict.fromkeys(first.concept_tags))
    assert newly_collected_tags(engine, first, ["lesson_01"]) == []
    second = engine.get("lesson_02")
    fresh = newly_collected_tags(engine, second, ["lesson_01"])
    assert set(fresh) == set(second.concept_tags) - set(first.concept_tags)


def test_album_line():
    assert album_line(0, 0) is None
    assert "first concept card" in album_line(0, 10)
    assert album_line(3, 10) == "3 of 10 cards collected."
    assert "Every card" in album_line(10, 10)
