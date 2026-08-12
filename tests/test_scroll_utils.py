"""Tests for the centralized, fast mouse-wheel scrolling handler.

Deliberately does NOT rely on synthetic <Enter>/<Leave> events -- testing
confirmed those don't reliably fire via event_generate even on a real,
mapped (non-withdrawn) window in this environment, which is exactly why
the fix moved away from an Enter/Leave-gated design to one that resolves
the target canvas directly from the wheel event's own event.widget instead.
"""
import customtkinter as ctk
import pytest

from app.ui.scroll_utils import (
    _PIXELS_PER_NOTCH,
    _find_enclosing_scrollable_canvas,
    install_fast_mousewheel_scrolling,
)


@pytest.fixture
def root():
    r = ctk.CTk()
    r.geometry("400x300+2000+2000")  # real, mapped window -- see module docstring
    yield r
    r.destroy()


def _make_tall_scrollable_frame(root, item_count=40, height=200, item_height=30):
    frame = ctk.CTkScrollableFrame(root, height=height)
    frame.pack(fill="both", expand=True)
    labels = []
    for i in range(item_count):
        label = ctk.CTkLabel(frame, text=f"Item {i}", height=item_height)
        label.pack(fill="x")
        labels.append(label)
    root.update()
    return frame, labels


def test_find_enclosing_scrollable_canvas_walks_up_from_a_deep_descendant(root):
    frame, labels = _make_tall_scrollable_frame(root)
    found = _find_enclosing_scrollable_canvas(labels[5])
    assert found is frame._parent_canvas


def test_find_enclosing_scrollable_canvas_returns_none_outside_any_frame(root):
    plain_label = ctk.CTkLabel(root, text="not in a scrollable frame")
    plain_label.pack()
    assert _find_enclosing_scrollable_canvas(plain_label) is None


def test_find_enclosing_scrollable_canvas_finds_the_innermost_of_nested_frames(root):
    outer, _ = _make_tall_scrollable_frame(root, item_count=5)
    inner = ctk.CTkScrollableFrame(outer, height=80)
    inner.pack(fill="x")
    inner_label = ctk.CTkLabel(inner, text="deep inside")
    inner_label.pack()
    root.update()

    found = _find_enclosing_scrollable_canvas(inner_label)
    assert found is inner._parent_canvas
    assert found is not outer._parent_canvas


def test_wheel_event_on_a_child_widget_scrolls_its_enclosing_frame(root):
    frame, labels = _make_tall_scrollable_frame(root, item_count=60)
    install_fast_mousewheel_scrolling(root)
    canvas = frame._parent_canvas

    before = canvas.yview()
    labels[10].event_generate("<MouseWheel>", delta=-120, when="now")
    root.update()
    after = canvas.yview()

    assert after != before


def test_one_notch_scrolls_a_meaningful_amount_not_a_tiny_fraction(root):
    """Regression test for the "scrolling is very slow" report."""
    frame, labels = _make_tall_scrollable_frame(root, item_count=60, height=200)
    install_fast_mousewheel_scrolling(root)
    canvas = frame._parent_canvas

    before_top = canvas.yview()[0]
    labels[10].event_generate("<MouseWheel>", delta=-120, when="now")
    root.update()
    after_top = canvas.yview()[0]

    assert after_top - before_top > 0.02, "one notch should move a noticeable amount, not a sliver"


def test_scroll_distance_in_pixels_is_similar_regardless_of_content_height(root):
    """The exact bug reported: two frames scrolling by very different real
    amounts for identical wheel input, because CTk's own per-frame
    yscrollincrement varies independently of content size."""
    short_frame, short_labels = _make_tall_scrollable_frame(root, item_count=15, height=150, item_height=60)
    tall_frame, tall_labels = _make_tall_scrollable_frame(root, item_count=200, height=150, item_height=30)
    install_fast_mousewheel_scrolling(root)

    def pixels_moved_by_one_notch(canvas, label):
        bbox = canvas.bbox("all")
        content_height = bbox[3] - bbox[1]
        before = canvas.yview()[0]
        label.event_generate("<MouseWheel>", delta=-120, when="now")
        root.update()
        after = canvas.yview()[0]
        return (after - before) * content_height

    short_pixels = pixels_moved_by_one_notch(short_frame._parent_canvas, short_labels[5])
    tall_pixels = pixels_moved_by_one_notch(tall_frame._parent_canvas, tall_labels[5])

    assert short_pixels > 20, "should be a real, fast movement, not a sliver"
    assert short_pixels == pytest.approx(tall_pixels, rel=0.3), (
        "the same wheel input should move roughly the same real distance regardless of content height"
    )
    assert short_pixels == pytest.approx(_PIXELS_PER_NOTCH, rel=0.3)


def test_scrolling_outside_any_scrollable_frame_does_not_raise(root):
    plain_label = ctk.CTkLabel(root, text="not scrollable")
    plain_label.pack()
    install_fast_mousewheel_scrolling(root)

    plain_label.event_generate("<MouseWheel>", delta=-120, when="now")
    root.update()  # should simply do nothing, not raise


def test_reinstalling_overrides_ctk_own_native_handler_added_by_a_new_frame(root):
    """Re-asserting the binding after a screen is (re)built must claim
    priority over whatever CTkScrollableFrame.__init__ just registered for
    its own new instance -- this is how the fix stays leak-free across
    navigations without needing per-frame cleanup."""
    install_fast_mousewheel_scrolling(root)
    frame, labels = _make_tall_scrollable_frame(root, item_count=60)
    # A fresh CTkScrollableFrame's own __init__ just re-registered its
    # native handler via bind_all(..., add=True). Re-installing ours must
    # still end up as the effective handler.
    install_fast_mousewheel_scrolling(root)

    canvas = frame._parent_canvas
    before_top = canvas.yview()[0]
    labels[10].event_generate("<MouseWheel>", delta=-120, when="now")
    root.update()
    after_top = canvas.yview()[0]

    # If CTk's own (un-overridden) handler were still in sole control, the
    # movement would be governed by its yscrollincrement-based formula
    # instead of ours -- assert our characteristic fast, pixel-based amount.
    bbox = canvas.bbox("all")
    content_height = bbox[3] - bbox[1]
    pixels_moved = (after_top - before_top) * content_height
    assert pixels_moved == pytest.approx(_PIXELS_PER_NOTCH, rel=0.3)
