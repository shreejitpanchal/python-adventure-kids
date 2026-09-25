from app.ui.color_utils import contrasting_text_color, darken, lighten, relative_luminance, with_alpha


def test_relative_luminance_white_is_max_black_is_min():
    assert relative_luminance("#FFFFFF") == 1.0
    assert relative_luminance("#000000") == 0.0


def test_contrasting_text_color_picks_dark_text_on_light_background():
    assert contrasting_text_color("#FFCA28") == "#232323"  # bright yellow -> dark text


def test_contrasting_text_color_picks_light_text_on_darker_background():
    assert contrasting_text_color("#7E57C2") == "#FFFFFF"  # medium purple -> white text


def test_every_category_color_has_readable_contrast_text():
    from app.engine.categories import CATEGORY_META

    for slug, meta in CATEGORY_META.items():
        text = contrasting_text_color(meta.color)
        bg_lum = relative_luminance(meta.color)
        text_lum = relative_luminance(text)
        assert abs(bg_lum - text_lum) > 0.3, f"{slug}'s color {meta.color} has weak text contrast"


def test_darken_moves_toward_black():
    original = "#4C97FF"
    darker = darken(original, 0.2)
    assert relative_luminance(darker) < relative_luminance(original)


def test_lighten_moves_toward_white():
    original = "#4C97FF"
    lighter = lighten(original, 0.2)
    assert relative_luminance(lighter) > relative_luminance(original)


def test_darken_and_lighten_stay_within_valid_hex_range():
    for hex_color in ["#000000", "#FFFFFF", "#4C97FF"]:
        for result in (darken(hex_color, 0.5), lighten(hex_color, 0.5)):
            assert len(result) == 7 and result.startswith("#")
            int(result[1:], 16)  # raises if not valid hex


def test_with_alpha_prefixes_the_alpha_byte_in_aarrggbb_order():
    assert with_alpha("#4C97FF", 1.0) == "#FF4C97FF"
    assert with_alpha("#4C97FF", 0.0) == "#004C97FF"
    assert with_alpha("#4c97ff", 0.5) == "#804C97FF"  # 0.5 * 255 rounds to 128 = 0x80


def test_with_alpha_clamps_out_of_range_opacity():
    assert with_alpha("#000000", 2.0) == "#FF000000"
    assert with_alpha("#000000", -1.0) == "#00000000"
