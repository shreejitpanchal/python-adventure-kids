"""scenery_flet: every World draws a horizon and motifs; scenes are seeded
and fit their canvas."""
from __future__ import annotations

import random

import flet as ft
import flet.canvas as cv

from app.engine.worlds import WORLDS
from app.ui.components import scenery_flet as scenery


def _all_shapes_are_canvas_shapes(shapes) -> bool:
    return all(isinstance(shape, (cv.Path, cv.Rect, cv.Circle, cv.Oval, cv.Line, cv.Arc)) for shape in shapes)


def test_every_world_has_its_own_scene_and_unknown_worlds_get_the_meadow():
    scenes = {scenery.scene_for_world(world.id) for world in WORLDS}
    assert len(scenes) == len(WORLDS)
    assert scenery.scene_for_world("uncharted") == scenery.DEFAULT_SCENE


def test_every_horizon_draws_something_across_the_width():
    for scene in scenery.WORLD_SCENES.values():
        shapes = scenery.horizon_shapes(scene, 600, scenery.HORIZON_HEIGHT, "#4F8FF7")
        assert shapes and _all_shapes_are_canvas_shapes(shapes), scene


def test_motifs_cycle_and_draw_at_the_given_spot():
    for scene in list(scenery.WORLD_SCENES.values()) + ["meadow", "unknown"]:
        for index in range(3):
            shapes = scenery.motif_shapes(scene, 100, 200, 40, "#4F8FF7", index)
            assert shapes and _all_shapes_are_canvas_shapes(shapes), (scene, index)


def test_scenery_is_seeded_by_world_and_keeps_motifs_off_the_road():
    first = scenery.scenery_shapes("logic_peaks", 300, 900, "#7E57C2", motif_count=6)
    second = scenery.scenery_shapes("logic_peaks", 300, 900, "#7E57C2", motif_count=6)
    assert len(first) == len(second) > 1 + len(scenery.horizon_shapes("peaks", 300, scenery.HORIZON_HEIGHT, "#7E57C2"))
    seeded = scenery.scenery_shapes("logic_peaks", 300, 900, "#7E57C2", motif_count=6, rng=random.Random(1))
    assert len(seeded) == len(first)
    ground = first[0]
    assert isinstance(ground, cv.Rect) and ground.width == 300 and ground.height == 900


def test_build_scenery_and_skyline_are_tagged_containers():
    backdrop = scenery.build_scenery("arcade_islands", 300, 700, "#26C6DA")
    assert isinstance(backdrop, ft.Container) and isinstance(backdrop.content, cv.Canvas)
    assert backdrop.data == {"kind": "scenery", "world": "arcade_islands", "scene": "islands"}
    assert (backdrop.width, backdrop.height) == (300, 700)

    skyline = scenery.build_skyline("scholar_tower", "#4F46E5")
    assert skyline.data == {"kind": "skyline", "world": "scholar_tower", "scene": "tower"}
    assert (skyline.left, skyline.right, skyline.bottom) == (0, 0, 0)
    assert skyline.height == scenery.SKYLINE_HEIGHT
    assert skyline.content.shapes, "drawn across the virtual width"
