from app.engine.outfits import OUTFITS, codey_accessory, get_outfit
from app.engine.titles import level_title


def test_catalogue_ids_are_unique_and_prices_positive():
    ids = [o.id for o in OUTFITS]
    assert len(ids) == len(set(ids))
    assert all(o.price > 0 and o.emoji and o.title for o in OUTFITS)
    prices = [o.price for o in OUTFITS]
    assert prices == sorted(prices), "cheapest first, so the shop reads as a ladder"


def test_get_outfit():
    assert get_outfit("crown").emoji == "👑"
    assert get_outfit("nope") is None


def test_codey_accessory_prefers_the_equipped_outfit_and_falls_back_to_the_title():
    assert codey_accessory("crown", 1) == "👑"
    assert codey_accessory(None, 1) == level_title(1).codey_accessory == ""
    assert codey_accessory(None, 3) == level_title(3).codey_accessory == "🧢"
    assert codey_accessory("removed_outfit", 3) == "🧢"
