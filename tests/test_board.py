import pytest
from solvechessdotcom import board


def test_notation_to_pixels_corners():
    assert board.convert_chess_notation_to_pixels('a', '1') == (0, 945)
    assert board.convert_chess_notation_to_pixels('h', '8') == (945, 0)
    assert board.convert_chess_notation_to_pixels('e', '6') == (540, 270)


def test_notation_to_pixels_invalid():
    with pytest.raises(ValueError):
        board.convert_chess_notation_to_pixels('z', '1')
    with pytest.raises(ValueError):
        board.convert_chess_notation_to_pixels('a', '9')


def test_piece_details_from_notation():
    piece_id, x, y = board.get_piece_details_from_notation('qe6')
    assert piece_id == '#queen'
    assert (x, y) == (540, 270)


def test_piece_details_invalid_piece():
    with pytest.raises(ValueError):
        board.get_piece_details_from_notation('xe6')


def test_points_to_move_endpoints():
    points = board._points_to_move(0, 945, 135, 810, 24)
    assert len(points) == 24
    assert points[0] == (0, 945)
    assert points[-1] == (135, 810)


def test_points_to_move_monotonic():
    points = board._points_to_move(0, 0, 270, 0, 24)
    xs = [p[0] for p in points]
    assert xs == sorted(xs)
