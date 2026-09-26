"""Generates the app icon -- a cute coiled Python snake in an explorer cap,
winking on a sunny sky -- and writes every size the app uses.

Pure Pillow, drawn at 4x and downsampled for smooth edges; no external art
assets, matching how the rest of the app is emoji/procedural only (see
scripts/generate_sounds.py for the same approach with audio). Re-run after
tweaking colors or shapes:

    .venv\\Scripts\\python.exe scripts\\generate_icon.py

Outputs (all overwritten):
    content/images/main-icon.png   512px -- CTk window/taskbar + in-UI (app/ui/assets.py)
    content/images/main-icon.ico   16..256px -- Windows .ico for the taskbar
    assets/main-icon.png           512px -- Flet page.window.icon (app_window_flet.py)
    assets/icon_android.png        512px -- Android launcher icon (build_apk.sh / pyproject)
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_512 = [
    REPO_ROOT / "content" / "images" / "main-icon.png",
    REPO_ROOT / "assets" / "main-icon.png",
    REPO_ROOT / "assets" / "icon_android.png",
]
ICO_OUTPUT = REPO_ROOT / "content" / "images" / "main-icon.ico"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

SIZE = 512
SCALE = 4  # supersampling factor
S = SIZE * SCALE

# Palette -- bright, saturated, kid-friendly.
SKY_TOP = (94, 212, 255)
SKY_BOTTOM = (43, 134, 240)
HILL = (92, 214, 108)
HILL_DARK = (58, 176, 84)
SNAKE = (76, 200, 96)
SNAKE_DARK = (34, 128, 62)
SNAKE_BELLY = (196, 244, 160)
CAP = (176, 108, 56)
CAP_DARK = (120, 70, 34)
CAP_BAND = (255, 203, 60)
EYE_WHITE = (255, 255, 255)
PUPIL = (36, 36, 48)
CHEEK = (255, 140, 150)
TONGUE = (255, 92, 108)
STAR = (255, 220, 70)
CLOUD = (255, 255, 255)


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _gradient(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        draw.line([(0, y), (width, y)], fill=_lerp(top, bottom, y / max(1, height - 1)))
    return img


def _squircle_mask(size: int, radius_ratio: float = 0.24) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255)
    return mask


def _bezier(p0, p1, p2, p3, steps: int = 200) -> list[tuple[float, float]]:
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _snake_path() -> list[tuple[float, float]]:
    """A chunky S-coil: tail bottom-left, sweeping up through the middle to
    the head at the upper right. Coordinates in the 0..1 unit square."""
    seg1 = _bezier((0.16, 0.80), (0.05, 0.50), (0.55, 0.42), (0.52, 0.62))
    seg2 = _bezier((0.52, 0.62), (0.50, 0.80), (0.92, 0.78), (0.80, 0.52))
    seg3 = _bezier((0.80, 0.52), (0.72, 0.34), (0.55, 0.30), (0.62, 0.30))
    return seg1 + seg2[1:] + seg3[1:]


def _draw_cloud(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    for dx, dy, k in ((-1.0, 0.25, 0.75), (0.0, 0.0, 1.0), (1.0, 0.2, 0.8), (0.5, 0.45, 0.7), (-0.5, 0.45, 0.7)):
        rr = r * k
        draw.ellipse([cx + dx * r - rr, cy + dy * r - rr, cx + dx * r + rr, cy + dy * r + rr], fill=CLOUD)


def _draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color) -> None:
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.45
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(points, fill=color)


def render(size: int = S) -> Image.Image:
    u = size  # unit multiplier for 0..1 coordinates

    # -- sky background inside a squircle -----------------------------------
    sky = _gradient(size, size, SKY_TOP, SKY_BOTTOM)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(sky, (0, 0), _squircle_mask(size))
    draw = ImageDraw.Draw(canvas)

    # sun glow, top-left
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([0.02 * u, 0.02 * u, 0.42 * u, 0.42 * u], fill=(255, 240, 160, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=size * 0.06))
    canvas = Image.alpha_composite(canvas, Image.composite(glow, Image.new("RGBA", (size, size), (0, 0, 0, 0)), _squircle_mask(size)))
    draw = ImageDraw.Draw(canvas)

    # clouds
    _draw_cloud(draw, 0.24 * u, 0.20 * u, 0.055 * u)
    _draw_cloud(draw, 0.78 * u, 0.15 * u, 0.045 * u)

    # rolling green hill along the bottom, clipped to the squircle
    hill_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hill_draw = ImageDraw.Draw(hill_layer)
    hill_draw.ellipse([-0.25 * u, 0.74 * u, 0.75 * u, 1.30 * u], fill=HILL_DARK + (255,))
    hill_draw.ellipse([0.20 * u, 0.78 * u, 1.30 * u, 1.35 * u], fill=HILL + (255,))
    hill_layer.putalpha(Image.composite(hill_layer.getchannel("A"), Image.new("L", (size, size), 0), _squircle_mask(size)))
    canvas = Image.alpha_composite(canvas, hill_layer)
    draw = ImageDraw.Draw(canvas)

    # -- the snake -------------------------------------------------------------
    # Drawn by stamping circles along the curve rather than one thick
    # polyline: Pillow's wide joined lines leave radial streaks on curves,
    # and stamping lets the tail taper naturally.
    path = [(x * u, y * u) for x, y in _snake_path()]
    body_w = 0.15 * u
    outline_w = 0.022 * u

    def body_radius(t: float) -> float:
        # thin tail tip growing to full thickness by a third of the way along
        return body_w / 2 * (0.30 + 0.70 * min(1.0, t / 0.35))

    def stamp(target: ImageDraw.ImageDraw, radius_of, fill, dx: float = 0.0, dy: float = 0.0, start: float = 0.0, end: float = 1.0) -> None:
        last = len(path) - 1
        for i, (x, y) in enumerate(path):
            t = i / last
            if t < start or t > end:
                continue
            r = radius_of(t)
            target.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=fill)

    # soft drop shadow
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    stamp(ImageDraw.Draw(shadow), lambda t: body_radius(t) + outline_w, (0, 40, 90, 110), dy=0.03 * u)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=size * 0.012))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    stamp(draw, lambda t: body_radius(t) + outline_w, SNAKE_DARK)
    stamp(draw, body_radius, SNAKE)
    # belly highlight: a thinner, lighter band nudged up-left, not on the tail tip
    stamp(draw, lambda t: body_radius(t) * 0.30, SNAKE_BELLY, dx=-0.012 * u, dy=-0.02 * u, start=0.12, end=0.94)

    # -- head ----------------------------------------------------------------------
    hx, hy = path[-1][0] + 0.02 * u, path[-1][1] - 0.02 * u
    head_r = 0.155 * u
    draw.ellipse([hx - head_r - outline_w, hy - head_r - outline_w, hx + head_r + outline_w, hy + head_r + outline_w], fill=SNAKE_DARK)
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=SNAKE)
    # lighter snout
    draw.ellipse([hx - head_r * 0.55, hy - head_r * 0.05, hx + head_r * 0.75, hy + head_r * 0.85], fill=_lerp(SNAKE, SNAKE_BELLY, 0.45))

    # explorer cap: dome + brim + band
    cap_top = hy - head_r * 1.05
    draw.chord([hx - head_r * 0.95, cap_top - head_r * 0.15, hx + head_r * 0.95, hy + head_r * 0.05], start=180, end=360, fill=CAP_DARK)
    draw.chord([hx - head_r * 0.88, cap_top - head_r * 0.08, hx + head_r * 0.88, hy - head_r * 0.02], start=180, end=360, fill=CAP)
    draw.rounded_rectangle([hx - head_r * 1.25, hy - head_r * 0.62, hx + head_r * 1.05, hy - head_r * 0.40], radius=int(head_r * 0.11), fill=CAP_DARK)
    draw.rounded_rectangle([hx - head_r * 0.9, hy - head_r * 0.72, hx + head_r * 0.9, hy - head_r * 0.58], radius=int(head_r * 0.07), fill=CAP_BAND)

    # eyes: left open and big, right winking
    ex, ey = hx - head_r * 0.30, hy - head_r * 0.15
    er = head_r * 0.30
    draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=EYE_WHITE)
    draw.ellipse([ex - er * 0.55 + er * 0.15, ey - er * 0.55, ex + er * 0.55 + er * 0.15, ey + er * 0.55], fill=PUPIL)
    draw.ellipse([ex + er * 0.05, ey - er * 0.45, ex + er * 0.40, ey - er * 0.10], fill=EYE_WHITE)
    wx, wy = hx + head_r * 0.42, hy - head_r * 0.15
    draw.arc([wx - er * 0.9, wy - er * 0.9, wx + er * 0.9, wy + er * 0.6], start=200, end=340, fill=PUPIL, width=int(outline_w * 1.1))

    # cheeks + smile + a little forked tongue poking out below the smile
    draw.ellipse([hx - head_r * 0.62, hy + head_r * 0.20, hx - head_r * 0.30, hy + head_r * 0.42], fill=CHEEK)
    draw.arc([hx - head_r * 0.35, hy + head_r * 0.05, hx + head_r * 0.60, hy + head_r * 0.75], start=20, end=160, fill=SNAKE_DARK, width=int(outline_w))
    tongue_x, tongue_y = hx + head_r * 0.14, hy + head_r * 0.72
    fork_y = tongue_y + head_r * 0.30
    draw.line([(tongue_x, tongue_y), (tongue_x, fork_y)], fill=TONGUE, width=int(outline_w * 0.9))
    draw.line([(tongue_x, fork_y), (tongue_x - head_r * 0.14, fork_y + head_r * 0.16)], fill=TONGUE, width=int(outline_w * 0.8))
    draw.line([(tongue_x, fork_y), (tongue_x + head_r * 0.14, fork_y + head_r * 0.16)], fill=TONGUE, width=int(outline_w * 0.8))

    # -- sparkle stars ---------------------------------------------------------------
    _draw_star(draw, 0.86 * u, 0.36 * u, 0.06 * u, STAR)
    _draw_star(draw, 0.14 * u, 0.44 * u, 0.035 * u, STAR)
    _draw_star(draw, 0.30 * u, 0.30 * u, 0.022 * u, (255, 255, 255))

    return canvas


def main() -> None:
    big = render()
    icon_512 = big.resize((SIZE, SIZE), Image.LANCZOS)
    for path in OUTPUTS_512:
        path.parent.mkdir(parents=True, exist_ok=True)
        icon_512.save(path, format="PNG", optimize=True)
        print(f"wrote {path.relative_to(REPO_ROOT)}")

    icon_256 = big.resize((256, 256), Image.LANCZOS)
    icon_256.save(ICO_OUTPUT, format="ICO", sizes=ICO_SIZES)
    print(f"wrote {ICO_OUTPUT.relative_to(REPO_ROOT)} ({len(ICO_SIZES)} sizes)")


if __name__ == "__main__":
    main()
