"""The shared game-world kit (app/ui/components/adventure_kit_flet.py) and
the theme sky colors it draws from."""
from __future__ import annotations

import dataclasses

import flet as ft

from app.ui.components.adventure_kit_flet import (
    RADIUS_CARD, SCREEN_PADDING, WIDE_BREAKPOINT, accent_gradient, emoji_badge, find_by_kind, hero_card,
    hero_header, iter_controls, layout_for, lip_shadow, plain_card, play_power_bar, power_bar, power_bar_fill,
    scene_view, sky_gradient, soft_shadow, stat_chip,
)
from app.ui.color_utils import relative_luminance
from app.ui.theme_flet import SKY_COLORS, THEME_PRESETS, get_preset, sky_colors
from tests.flet_testing import FakePage, NoTaskPage, one

THEME = get_preset("forest_adventure")


def test_every_preset_has_sky_colors_and_they_match_the_preset_mode():
    for key, preset in THEME_PRESETS.items():
        assert key in SKY_COLORS, f"{key} needs a SKY_COLORS entry"
        top, bottom = sky_colors(preset)
        assert bottom == preset.bg, "the sky must fade into the preset's own bg"
        top_is_dark = relative_luminance(top) < 0.5
        assert top_is_dark == preset.is_dark, f"{key}: sky top should match the preset's light/dark mode"


def test_unknown_preset_falls_back_to_card_into_bg():
    custom = dataclasses.replace(THEME, key="brand_new")
    assert sky_colors(custom) == (custom.card, custom.bg)


def test_sky_gradient_runs_top_to_bottom_with_the_sky_colors():
    gradient = sky_gradient(THEME)
    assert isinstance(gradient, ft.LinearGradient)
    assert gradient.colors == list(sky_colors(THEME))


def test_accent_gradient_is_lighter_at_the_start_than_the_end():
    gradient = accent_gradient("#4C97FF")
    assert len(gradient.colors) == 2
    assert relative_luminance(gradient.colors[0]) > relative_luminance(gradient.colors[1])


def test_shadows():
    soft = soft_shadow("#4C97FF", opacity=0.5, blur=12, dy=6)
    assert soft.color.startswith("#80")  # alpha byte first
    assert soft.blur_radius == 12 and soft.offset.y == 6
    lip = lip_shadow("#4C97FF", depth=5)
    assert lip.blur_radius == 0 and lip.offset.y == 5
    assert relative_luminance(lip.color) < relative_luminance("#4C97FF")


def test_scene_view_uses_the_theme_bg_and_leaves_bottom_clearance():
    view = scene_view("/x", THEME, [ft.Text("hi")])
    assert view.route == "/x"
    assert view.bgcolor == THEME.bg
    assert view.scroll == ft.ScrollMode.AUTO
    assert view.padding.bottom > view.padding.left


def test_hero_header_carries_title_buttons_and_companion():
    companion = ft.Text("codey", data={"kind": "companion_stub"})
    header = hero_header(THEME, title="Hello", scale=1.0, buttons=[ft.Button("b")], companion=companion)
    assert header.data == {"kind": "hero_header", "title": "Hello"}
    assert header.gradient is not None
    assert one(header, "companion_stub") is companion
    assert any(isinstance(c, ft.Button) for c in iter_controls(header))


def test_stat_chip_and_emoji_badge_data():
    chip = stat_chip(THEME, "⭐", "3 stars", 1.0, kind="stars")
    assert chip.data == {"kind": "stars", "label": "3 stars"}
    assert chip.content.controls[1].value == "3 stars"
    badge = emoji_badge("🚀", size=48, bgcolor="#4C97FF")
    assert badge.width == badge.height == 48
    assert badge.content.value == "🚀"


def test_power_bar_clamps_ratio_and_sizes_the_fill():
    bar = power_bar(THEME, 0.25, width=200, height=10)
    assert bar.data["ratio"] == 0.25
    assert power_bar_fill(bar).width == 50
    assert power_bar(THEME, 7.0, width=200).data["ratio"] == 1.0
    assert power_bar(THEME, -1.0, width=200).data["ratio"] == 0.0


def test_play_power_bar_parks_the_fill_and_schedules_growth_when_it_can():
    page = FakePage()
    bar = power_bar(THEME, 0.5, width=200)
    assert play_power_bar(page, bar) is True
    assert power_bar_fill(bar).width == 0
    (handler, args, _kwargs), = page.run_task_calls
    assert handler.__name__ == "_grow_fill"
    assert args[2] == 100  # the real width, restored by the task


def test_play_power_bar_leaves_the_fill_alone_when_it_cannot_animate_or_is_empty():
    bar = power_bar(THEME, 0.5, width=200)
    assert play_power_bar(NoTaskPage(), bar) is False
    assert power_bar_fill(bar).width == 100
    empty = power_bar(THEME, 0.0, width=200)
    assert play_power_bar(FakePage(), empty) is False


def test_hero_card_featured_gets_a_rim_and_is_clickable_only_with_a_handler():
    clicks = []
    featured = hero_card(THEME, accent="#4C97FF", children=[ft.Text("t")], on_click=lambda e: clicks.append(e), featured=True, data={"kind": "x"})
    assert featured.border is not None and featured.ink is True
    assert featured.border_radius == RADIUS_CARD
    featured.on_click("e")
    assert clicks == ["e"]
    plain = hero_card(THEME, accent="#4C97FF", children=[ft.Text("t")])
    assert plain.border is None and plain.ink is False and plain.on_click is None


def test_layout_for_is_compact_without_a_width_and_wide_from_the_breakpoint():
    compact = layout_for(FakePage())
    assert compact.wide is False and compact.card_width is None and compact.map_lanes == 2
    assert compact.content_width is None

    narrow = FakePage()
    narrow.width = WIDE_BREAKPOINT - 1
    assert layout_for(narrow).wide is False

    wide_page = FakePage()
    wide_page.width = 1200
    wide = layout_for(wide_page)
    assert wide.wide is True and wide.card_width == 340 and wide.map_lanes == 3
    assert wide.content_width == 880 and wide.map_width == 620

    modest = FakePage()
    modest.width = 800
    assert layout_for(modest).content_width == 800 - 2 * SCREEN_PADDING


def test_scene_view_centers_and_caps_content_only_when_wide():
    controls = [ft.Text("a"), ft.Text("b")]
    compact = scene_view("/x", THEME, controls, page=FakePage())
    assert compact.controls == controls

    page = FakePage()
    page.width = 1200
    wide = scene_view("/x", THEME, controls, page=page)
    column = one(wide, "content_column")
    assert column.width == 880 and column.controls == controls


def test_plain_card_and_find_by_kind_walk_nested_content_and_controls():
    inner = ft.Text("deep", data={"kind": "needle"})
    card = plain_card(THEME, [ft.Row([ft.Container(content=ft.Column([inner]))])], data={"kind": "card"})
    assert find_by_kind(card, "needle") == [inner]
    assert find_by_kind(card, "card") == [card]
    assert find_by_kind(card, "missing") == []
