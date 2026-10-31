"""Concept cards: one collectible per concept tag, earned the first time a
lesson carrying that tag is completed and "leveled" by every further
lesson with it. Derived entirely from Lesson.concept_tags and the
completed-lesson list -- no card table, nothing to migrate -- so adding a
tag to lesson YAML adds a card automatically. CARD_META only decorates the
tags it knows; an unknown tag still becomes a card with a generic look.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Optional


@dataclass(frozen=True)
class CardMeta:
    title: str
    icon: str
    color: str
    blurb: str


CARD_META: dict[str, CardMeta] = {
    "print": CardMeta("Printer", "🖨️", "#4F8FF7", "Makes Python talk."),
    "strings": CardMeta("String Weaver", "🧵", "#EC407A", "Words, letters and quotes."),
    "variables": CardMeta("Box Keeper", "📦", "#FF9F1C", "Names that remember things."),
    "numbers": CardMeta("Number Knight", "🔢", "#FFB238", "Counting, adding, dividing."),
    "expressions": CardMeta("Math Wizard", "🧮", "#F4A261", "Sums that Python works out."),
    "input": CardMeta("Question Asker", "🙋", "#26C6DA", "Lets the player type back."),
    "conditionals": CardMeta("Decision Maker", "🚦", "#7E57C2", "if, elif, else."),
    "comparison": CardMeta("Judge", "⚖️", "#9575CD", "Bigger, smaller, equal?"),
    "booleans": CardMeta("Truth Teller", "✅", "#66BB6A", "True or False."),
    "loops": CardMeta("Loop Rider", "🔁", "#42A5F5", "Doing it again and again."),
    "for-loops": CardMeta("For Ranger", "🏹", "#29B6F6", "Walks through every item."),
    "while-loops": CardMeta("While Watcher", "⏳", "#26A69A", "Keeps going until it's time to stop."),
    "iteration": CardMeta("Step Walker", "👣", "#00ACC1", "One item at a time."),
    "functions": CardMeta("Spell Crafter", "🪄", "#AB47BC", "Reusable blocks of code."),
    "parameters": CardMeta("Ingredient Chef", "🥕", "#BA68C8", "What a function takes in."),
    "return-values": CardMeta("Gift Giver", "🎁", "#CE93D8", "What a function hands back."),
    "lists": CardMeta("List Collector", "📋", "#5C6BC0", "Many things in one line."),
    "indexing": CardMeta("Index Finger", "👉", "#7986CB", "Picking item number n."),
    "slicing": CardMeta("Slicer", "🔪", "#9FA8DA", "A piece of a list or string."),
    "dictionaries": CardMeta("Key Master", "🗝️", "#8D6E63", "Keys that open values."),
    "tuples": CardMeta("Tuple Twins", "👯", "#A1887F", "Pairs that never change."),
    "sets": CardMeta("Set Sorter", "🧺", "#BCAAA4", "No duplicates allowed."),
    "f-strings": CardMeta("Format Fox", "🦊", "#FF7043", "Words with values inside."),
    "type-conversion": CardMeta("Shape Shifter", "🔄", "#FFA726", "int, str, float."),
    "errors": CardMeta("Bug Hunter", "🐛", "#D4A017", "Reads what went wrong."),
    "debugging": CardMeta("Detective", "🔍", "#C0A000", "Finds and fixes the bug."),
    "random": CardMeta("Dice Roller", "🎲", "#EF5350", "Surprises every run."),
    "games": CardMeta("Game Maker", "🕹️", "#E53935", "Turns code into play."),
    "recursion": CardMeta("Mirror Mage", "🪞", "#8E24AA", "A function that calls itself."),
    "algorithms": CardMeta("Pathfinder", "🧭", "#3949AB", "Step-by-step recipes."),
    "classes": CardMeta("Blueprint Builder", "🏗️", "#00897B", "Makes new kinds of things."),
    "async": CardMeta("Time Juggler", "🤹", "#039BE5", "Many things at once."),
    "ai": CardMeta("Thinking Machine", "🤖", "#7C4DFF", "Computers that learn."),
    "machine-learning": CardMeta("Pattern Finder", "📈", "#651FFF", "Learning from examples."),
    "neural-networks": CardMeta("Brain Weaver", "🧠", "#6200EA", "Layers of tiny decisions."),
}

DEFAULT_CARD_COLOR = "#78909C"


def card_meta(tag: str) -> CardMeta:
    """Decoration for a tag; an unknown tag gets a generic card named after
    itself so nothing earned is ever hidden."""
    meta = CARD_META.get(tag)
    if meta is not None:
        return meta
    return CardMeta(tag.replace("-", " ").title(), "🃏", DEFAULT_CARD_COLOR, "A concept you've met in a lesson.")


@dataclass(frozen=True)
class ConceptCard:
    tag: str
    meta: CardMeta
    level: int
    """How many completed lessons carry the tag (0 = not yet collected)."""
    total: int
    """How many lessons in the whole curriculum carry it."""

    @property
    def collected(self) -> bool:
        return self.level > 0

    @property
    def rarity(self) -> str:
        """Tags taught by few lessons are the rare cards."""
        if self.total <= 3:
            return "legendary"
        if self.total <= 10:
            return "rare"
        return "common"

    @property
    def maxed(self) -> bool:
        return self.total > 0 and self.level >= self.total


def _tags_by_lesson(engine) -> dict[str, list[str]]:
    return {lesson.id: list(lesson.concept_tags or []) for lesson in engine.all_in_order()}


def all_cards(engine, completed_ids: Collection[str]) -> list[ConceptCard]:
    """Every card the curriculum can produce, collected or not, most common
    tags first (so a fresh album opens on the cards a child will earn
    soonest) and alphabetical within a tie."""
    completed = set(completed_ids)
    totals: dict[str, int] = {}
    levels: dict[str, int] = {}
    for lesson_id, tags in _tags_by_lesson(engine).items():
        for tag in set(tags):
            totals[tag] = totals.get(tag, 0) + 1
            if lesson_id in completed:
                levels[tag] = levels.get(tag, 0) + 1
    ordered = sorted(totals, key=lambda tag: (-totals[tag], tag))
    return [ConceptCard(tag, card_meta(tag), levels.get(tag, 0), totals[tag]) for tag in ordered]


def collected_cards(engine, completed_ids: Collection[str]) -> list[ConceptCard]:
    return [card for card in all_cards(engine, completed_ids) if card.collected]


def newly_collected_tags(engine, lesson, completed_before: Collection[str]) -> list[str]:
    """Tags on `lesson` that no previously completed lesson carried -- the
    cards this pass just unlocked, in the lesson's own tag order."""
    before = {card.tag for card in collected_cards(engine, completed_before)}
    seen: set[str] = set()
    fresh: list[str] = []
    for tag in lesson.concept_tags or []:
        if tag not in before and tag not in seen:
            seen.add(tag)
            fresh.append(tag)
    return fresh


def album_line(collected: int, total: int) -> Optional[str]:
    if total == 0:
        return None
    if collected == 0:
        return "Finish a lesson to earn your first concept card!"
    if collected == total:
        return "Every card collected — the whole curriculum in your pocket! 🃏"
    return f"{collected} of {total} cards collected."
