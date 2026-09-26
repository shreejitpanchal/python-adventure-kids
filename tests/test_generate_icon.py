"""Smoke test for scripts/generate_icon.py's renderer -- it's a build-time
asset generator, not app code, but a broken render would silently ship a
blank icon, so check the essentials without touching the real files."""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_icon", REPO_ROOT / "scripts" / "generate_icon.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_render_produces_a_squircle_with_a_green_snake_on_a_sky():
    generator = _load_generator()
    image = generator.render(size=256)

    assert image.size == (256, 256) and image.mode == "RGBA"
    # Rounded corners are transparent, the middle is opaque.
    assert image.getpixel((0, 0))[3] == 0
    assert image.getpixel((255, 255))[3] == 0
    assert image.getpixel((128, 128))[3] == 255
    # Sky at the top edge centre, snake green somewhere along the coil.
    r, g, b, _ = image.getpixel((128, 6))
    assert b > r, "top of the icon should be sky blue"
    r, g, b, _ = image.getpixel((150, 160))
    assert g > r and g > b, "the coil should be green"


def test_generated_files_are_the_ones_the_app_loads():
    generator = _load_generator()
    outputs = {path.relative_to(REPO_ROOT).as_posix() for path in generator.OUTPUTS_512}
    assert outputs == {"content/images/main-icon.png", "assets/main-icon.png", "assets/icon_android.png"}
    assert generator.ICO_OUTPUT.relative_to(REPO_ROOT).as_posix() == "content/images/main-icon.ico"
    assert (16, 16) in generator.ICO_SIZES and (256, 256) in generator.ICO_SIZES
