from app.ui.adventure_map_layout import (
    CAPTION_HEIGHT,
    LEFT_MARGIN,
    NODE_SIZE,
    PATH_WIDTH,
    ROW_HEIGHT,
    TOP_MARGIN,
    total_path_height,
    zigzag_positions,
)


def test_zigzag_positions_empty_for_zero_nodes():
    assert zigzag_positions(0) == []


def test_first_node_is_on_the_left():
    positions = zigzag_positions(1)
    assert positions[0].x == LEFT_MARGIN
    assert positions[0].y == TOP_MARGIN


def test_nodes_alternate_left_and_right():
    positions = zigzag_positions(4)
    right_x = PATH_WIDTH - NODE_SIZE - LEFT_MARGIN
    assert [p.x for p in positions] == [LEFT_MARGIN, right_x, LEFT_MARGIN, right_x]


def test_nodes_descend_one_row_each():
    positions = zigzag_positions(3)
    assert [p.y for p in positions] == [TOP_MARGIN, TOP_MARGIN + ROW_HEIGHT, TOP_MARGIN + 2 * ROW_HEIGHT]


def test_center_properties_are_offset_by_half_node_size():
    position = zigzag_positions(1)[0]
    assert position.center_x == LEFT_MARGIN + NODE_SIZE / 2
    assert position.center_y == TOP_MARGIN + NODE_SIZE / 2


def test_total_path_height_zero_nodes_is_just_the_margin():
    assert total_path_height(0) == TOP_MARGIN


def test_total_path_height_grows_with_row_count():
    h1 = total_path_height(1)
    h2 = total_path_height(2)
    assert h2 - h1 == ROW_HEIGHT
    assert h1 == TOP_MARGIN + NODE_SIZE + CAPTION_HEIGHT
