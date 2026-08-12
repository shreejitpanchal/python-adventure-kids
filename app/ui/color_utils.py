"""Small color-math helpers for category color-coding (Scratch-style solid,
distinct colors per topic) -- no external deps, just RGB arithmetic."""
from __future__ import annotations


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, c)) for c in rgb))


def relative_luminance(hex_color: str) -> float:
    r, g, b = (c / 255.0 for c in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrasting_text_color(hex_color: str, light: str = "#FFFFFF", dark: str = "#232323") -> str:
    """Picks white or near-black text depending on which reads better on this background."""
    return dark if relative_luminance(hex_color) > 0.6 else light


def shade(hex_color: str, factor: float) -> str:
    """factor > 0 lightens toward white, factor < 0 darkens toward black. Range: -1..1."""
    r, g, b = _hex_to_rgb(hex_color)
    if factor >= 0:
        r = r + (255 - r) * factor
        g = g + (255 - g) * factor
        b = b + (255 - b) * factor
    else:
        r = r * (1 + factor)
        g = g * (1 + factor)
        b = b * (1 + factor)
    return _rgb_to_hex((round(r), round(g), round(b)))


def darken(hex_color: str, amount: float = 0.15) -> str:
    return shade(hex_color, -abs(amount))


def lighten(hex_color: str, amount: float = 0.15) -> str:
    return shade(hex_color, abs(amount))
