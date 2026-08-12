from app.ui.color_utils import contrasting_text_color, darken, lighten, relative_luminance


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
