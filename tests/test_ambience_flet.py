"""ambience_flet: the time-of-day sky behind hero headers and the per-World
weather over map roads. Scenes are seeded, so the same inputs give the
same particles; a page that can animate gets bounded drift/twinkle/bob
tasks, one that can't gets a still scene."""
from __future__ import annotations

import random

import flet as ft

from app.engine.worlds import WORLDS
from app.ui.components import ambience_flet as ambience
from app.ui.components import motion_flet as motion
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, NoTaskPage, all_of, one

THEME = get_preset("sunny_light")


def test_sky_moment_by_hour():
    assert ambience.sky_moment(6).name == "dawn"
    assert ambience.sky_moment(12).name == "day"
    assert ambience.sky_moment(18).name == "dusk"
    assert ambience.sky_moment(23).name == "night"
    assert ambience.sky_moment(2).name == "night"
    assert ambience.sky_moment(26).name == "night", "hours wrap"
    assert ambience.sky_moment().name in ambience.SKY_MOMENTS, "no hour -> the clock"


def test_backdrop_is_positioned_fill_with_the_moments_decorations():
    backdrop = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["night"])
    assert isinstance(backdrop, ft.Stack)
    assert (backdrop.left, backdrop.top, backdrop.right, backdrop.bottom) == (0, 0, 0, 0)
    assert backdrop.data == {"kind": "sky_backdrop", "moment": "night", "sparkles": False}
    particles = all_of(backdrop, "sky_particle")
    assert [p.data["emoji"] for p in particles] == list(ambience.SKY_MOMENTS["night"].emoji)
    # Alternating anchors so the decorations spread across any header width.
    assert all((p.left is None) != (p.right is None) for p in particles)
    assert all(p.top is not None for p in particles)


def test_night_and_dusk_tint_the_sky_but_day_does_not():
    assert len(all_of(ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["night"]), "sky_tint")) == 1
    assert len(all_of(ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["dusk"]), "sky_tint")) == 1
    assert all_of(ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"]), "sky_tint") == []


def test_backdrop_is_deterministic_for_a_moment():
    first = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"])
    second = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"])
    layout = lambda stack: [(p.left, p.right, p.top) for p in all_of(stack, "sky_particle")]  # noqa: E731
    assert layout(first) == layout(second)
    seeded = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"], rng=random.Random(99))
    assert layout(seeded) != layout(first)


def test_sparkles_are_added_only_when_asked_and_rise():
    plain = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"])
    assert all_of(plain, "sky_sparkle") == []

    page = FakePage()
    hub = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["day"], sparkles=True, page=page)
    sparkles = all_of(hub, "sky_sparkle")
    assert len(sparkles) == ambience.SPARKLE_COUNT
    # Each sparkle drifts upward and twinkles.
    rising = [args for args, _kwargs in page.scheduled(motion._drift) if args[1] in sparkles]
    assert len(rising) == ambience.SPARKLE_COUNT
    assert all(args[4] < 0 for args in rising), "dy is negative: they float up"
    assert len([1 for args, _k in page.scheduled(motion._twinkle) if args[1] in sparkles]) == ambience.SPARKLE_COUNT


def test_decorations_animate_by_kind_and_stand_still_without_a_page():
    page = FakePage()
    night = ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["night"], page=page)
    particles = {p.data["emoji"]: p for p in all_of(night, "sky_particle")}
    bobbing = [args[1] for args, _k in page.scheduled(motion._bob)]
    twinkling = [args[1] for args, _k in page.scheduled(motion._twinkle)]
    assert particles["🌙"] in bobbing
    assert particles["⭐"] in twinkling

    still = NoTaskPage()
    ambience.build_sky_backdrop(THEME, moment=ambience.SKY_MOMENTS["night"], page=still)
    assert still.run_task_calls == []


def test_every_world_has_its_own_weather_and_unknown_worlds_get_the_default():
    seen = set()
    for world in WORLDS:
        emoji = ambience.world_ambience_emoji(world.id)
        assert emoji, world.id
        seen.add(emoji)
    assert len(seen) == len(WORLDS), "each world's weather should look different"
    assert ambience.world_ambience_emoji("uncharted") == ambience.DEFAULT_AMBIENCE


def test_world_ambience_particles_fit_the_road_and_are_seeded_by_world():
    width, height = 300.0, 600.0
    particles = ambience.build_world_ambience("logic_peaks", width, height)
    assert len(particles) == len(ambience.WORLD_AMBIENCE["logic_peaks"])
    for particle in particles:
        assert particle.data["kind"] == "world_ambience" and particle.data["world"] == "logic_peaks"
        assert 0 <= particle.left <= width - 40
        assert 0 <= particle.top <= height - 70
        assert particle.opacity < 1.0, "weather sits behind the nodes, translucent"
    again = ambience.build_world_ambience("logic_peaks", width, height)
    assert [(p.left, p.top) for p in again] == [(p.left, p.top) for p in particles]
    assert [(p.left, p.top) for p in ambience.build_world_ambience("word_valley", width, height)] != [
        (p.left, p.top) for p in particles
    ]


def test_snow_falls_and_leaves_drift():
    page = FakePage()
    snow = ambience.build_world_ambience("logic_peaks", 300, 600, page=page, count=2)
    drifts = [args for args, _k in page.scheduled(motion._drift)]
    assert len(drifts) == 2
    assert all(args[4] > 0 for args in drifts), "snow: positive dy"
    assert all(args[1] in snow for args in drifts)

    leaves_page = FakePage()
    ambience.build_world_ambience("word_valley", 300, 600, page=leaves_page, count=1)
    ((args, _k),) = leaves_page.scheduled(motion._drift)
    assert args[4] == 0.0 and args[3] > 0, "leaves: sideways only"


def test_count_repeats_the_set_and_a_tiny_road_still_places_particles():
    particles = ambience.build_world_ambience("bug_swamp", 20, 20, count=7)
    assert len(particles) == 7
    assert all(p.left >= 0 and p.top >= 0 for p in particles)
    assert one(ft.Stack(particles[:1]), "world_ambience") is particles[0]
