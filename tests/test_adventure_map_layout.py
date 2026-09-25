from app.ui.adventure_map_layout import (
    CAPTION_HEIGHT,
    LEFT_MARGIN,
    MARKER_SIZE,
    NODE_LIP,
    NODE_SIZE,
    PATH_WIDTH,
    ROW_HEIGHT,
    TOP_MARGIN,
    curve_control_points,
    marker_position,
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
    assert h1 == TOP_MARGIN + NODE_SIZE + NODE_LIP + CAPTION_HEIGHT


def test_nodes_stay_inside_the_path_width():
    for position in zigzag_positions(5):
        assert 0 <= position.x
        assert position.x + NODE_SIZE <= PATH_WIDTH


def test_curve_control_points_leave_and_arrive_vertically():
    a, b = zigzag_positions(2)
    cp1_x, cp1_y, cp2_x, cp2_y = curve_control_points(a, b)
    mid_y = (a.center_y + b.center_y) / 2
    # First handle straight below the start node, second straight above the end node.
    assert (cp1_x, cp1_y) == (a.center_x, mid_y)
    assert (cp2_x, cp2_y) == (b.center_x, mid_y)


def test_marker_position_is_centered_above_the_node_and_inside_the_top_margin():
    node = zigzag_positions(1)[0]
    left, top = marker_position(node)
    assert left + MARKER_SIZE / 2 == node.center_x
    assert top >= 0, "TOP_MARGIN must leave room for the marker above the first node"
    assert top < node.y
