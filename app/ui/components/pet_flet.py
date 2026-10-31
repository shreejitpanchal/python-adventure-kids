"""Codey's buddy on screen: the creature from app/engine/pet.py drawn on a
flet.canvas (an egg with a crack, then a round-bodied critter that gains a
leaf, ears and a tail, wings, and finally a crown and glow as it grows),
in a chunky card with a power bar to the next stage. Rules live in the
engine; this draws. Flet only.
"""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

from app.engine.pet import PetStage, pet_line, pet_progress, pet_stage
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, darken, lighten, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import RADIUS_CARD, accent_gradient, lip_shadow, play_power_bar, power_bar, pressable, soft_shadow
from app.ui.theme_flet import scaled

PET_CANVAS = 96.0


def _paint(color: str, *, stroke: float | None = None) -> ft.Paint:
    if stroke is None:
        return ft.Paint(color=color, style=ft.PaintingStyle.FILL)
    return ft.Paint(color=color, style=ft.PaintingStyle.STROKE, stroke_width=stroke, stroke_cap=ft.StrokeCap.ROUND)


def pet_shapes(stage: PetStage, color: str, *, canvas: float = PET_CANVAS) -> list:
    """The buddy at `stage`, centered in a `canvas` px square. Each stage
    adds a feature on top of the last so growth is visibly cumulative."""
    c = canvas / 2
    body = float(stage.size)
    dark = darken(color, 0.5)
    shapes: list = []
    if stage.id == "egg":
        shapes.append(cv.Oval(c - body * 0.38, c - body * 0.5, body * 0.76, body, paint=_paint(lighten(color, 0.45))))
        zig = [cv.Path.MoveTo(c - body * 0.25, c)]
        for i in range(1, 6):
            zig.append(cv.Path.LineTo(c - body * 0.25 + i * body * 0.1, c + (body * 0.08 if i % 2 else -body * 0.04)))
        shapes.append(cv.Path(zig, paint=_paint(dark, stroke=2.5)))
        shapes.append(cv.Circle(c - body * 0.12, c - body * 0.2, body * 0.05, paint=_paint("#FFFFFF")))
        return shapes

    rank = ["hatchling", "sprout", "scamp", "guardian", "legend"].index(stage.id)
    if rank >= 4:
        shapes.append(cv.Circle(c, c, body * 0.62, paint=_paint(with_alpha("#FFD866", 0.35))))
    if rank >= 3:
        wing = _paint(lighten(color, 0.3))
        for direction in (-1, 1):
            shapes.append(cv.Path([
                cv.Path.MoveTo(c + direction * body * 0.35, c),
                cv.Path.QuadraticTo(c + direction * body * 0.8, c - body * 0.5, c + direction * body * 0.6, c + body * 0.15),
                cv.Path.Close(),
            ], paint=wing))
    if rank >= 2:
        shapes.append(cv.Path([
            cv.Path.MoveTo(c - body * 0.35, c + body * 0.15),
            cv.Path.QuadraticTo(c - body * 0.7, c + body * 0.3, c - body * 0.55, c - body * 0.15),
        ], paint=_paint(color, stroke=max(3.0, body * 0.08))))
        for direction in (-1, 1):
            shapes.append(cv.Path([
                cv.Path.MoveTo(c + direction * body * 0.28, c - body * 0.3),
                cv.Path.LineTo(c + direction * body * 0.42, c - body * 0.62),
                cv.Path.LineTo(c + direction * body * 0.1, c - body * 0.42),
                cv.Path.Close(),
            ], paint=_paint(color)))
    shapes.append(cv.Circle(c, c, body * 0.4, paint=_paint(color)))
    shapes.append(cv.Oval(c - body * 0.22, c + body * 0.02, body * 0.44, body * 0.3, paint=_paint(lighten(color, 0.4))))
    if rank >= 1:
        shapes.append(cv.Path([
            cv.Path.MoveTo(c, c - body * 0.4), cv.Path.QuadraticTo(c + body * 0.05, c - body * 0.6, c + body * 0.15, c - body * 0.68),
        ], paint=_paint(darken("#3FC97A", 0.1), stroke=3)))
        shapes.append(cv.Oval(c + body * 0.1, c - body * 0.82, body * 0.26, body * 0.16, paint=_paint("#3FC97A")))
    white = _paint("#FFFFFF")
    for direction in (-1, 1):
        shapes.append(cv.Circle(c + direction * body * 0.15, c - body * 0.08, body * 0.1, paint=white))
        shapes.append(cv.Circle(c + direction * body * 0.15, c - body * 0.07, body * 0.05, paint=_paint(dark)))
    shapes.append(cv.Path([
        cv.Path.MoveTo(c - body * 0.08, c + body * 0.12), cv.Path.QuadraticTo(c, c + body * 0.2, c + body * 0.08, c + body * 0.12),
    ], paint=_paint(dark, stroke=2.5)))
    if rank >= 4:
        crown = _paint("#FFD866")
        top = c - body * 0.4
        shapes.append(cv.Path([
            cv.Path.MoveTo(c - body * 0.22, top), cv.Path.LineTo(c - body * 0.22, top - body * 0.22),
            cv.Path.LineTo(c - body * 0.1, top - body * 0.1), cv.Path.LineTo(c, top - body * 0.26),
            cv.Path.LineTo(c + body * 0.1, top - body * 0.1), cv.Path.LineTo(c + body * 0.22, top - body * 0.22),
            cv.Path.LineTo(c + body * 0.22, top), cv.Path.Close(),
        ], paint=crown))
    return shapes


def build_pet_canvas(stage: PetStage, color: str) -> ft.Container:
    return ft.Container(
        content=cv.Canvas(shapes=pet_shapes(stage, color), width=PET_CANVAS, height=PET_CANVAS),
        width=PET_CANVAS, height=PET_CANVAS,
        data={"kind": "pet_canvas", "stage": stage.id},
    )


def build_pet_card(page, state: AppState, *, scale: float, on_click=None) -> ft.Container:
    """"Your buddy": the drawn creature bobbing beside its name, stage and
    the XP bar to the next stage."""
    theme = state.theme
    fs = lambda base: scaled(base, scale)  # noqa: E731
    total_xp = state.progress.get_player_level().total_xp
    stage = pet_stage(total_xp)
    into, span = pet_progress(total_xp)
    ratio = into / span if span else 1.0
    accent = lighten(theme.primary, 0.1)
    text_color = contrasting_text_color(accent)

    creature = build_pet_canvas(stage, theme.success if stage.id != "egg" else theme.warning)
    motion.prepare_bob(creature)
    if page is not None:
        motion.bob(page, creature, times=5, dy=0.06)

    bar = power_bar(theme, ratio, color=theme.star, width=200, height=10)
    play_power_bar(page, bar)
    card = ft.Container(
        content=ft.Row(
            [
                creature,
                ft.Column(
                    [
                        ft.Text("Your buddy", size=fs(11), color=text_color),
                        ft.Text(f"{stage.emoji} {stage.name}", size=fs(18), weight=ft.FontWeight.BOLD, color=text_color),
                        ft.Text(stage.description, size=fs(12), color=text_color),
                        bar,
                        ft.Text(pet_line(total_xp), size=fs(11), italic=True, color=text_color),
                    ],
                    spacing=3, expand=True,
                ),
            ],
            spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=accent_gradient(accent), border_radius=RADIUS_CARD, padding=16,
        shadow=[lip_shadow(accent, depth=6), soft_shadow(accent, opacity=0.25)],
        on_click=on_click, ink=on_click is not None,
        data={"kind": "pet_card", "stage": stage.id, "total_xp": total_xp},
    )
    if on_click is not None and page is not None:
        pressable(card, page, state=state)
    return card
