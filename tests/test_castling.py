from solvechessdotcom.castling import detect_castling


def test_white_kingside():
    assert detect_castling(['ke1', 'rh1', 'ra1'], 'e1g1', 'k', 'white') == 'h1f1'


def test_white_queenside():
    assert detect_castling(['ke1', 'ra1'], 'e1c1', 'k', 'white') == 'a1d1'


def test_black_kingside():
    # Regression: scraped positions are lowercase for both colors,
    # black castling used to look for an uppercase rook and always fail
    assert detect_castling(['ke8', 'rh8'], 'e8g8', 'k', 'black') == 'h8f8'


def test_black_queenside():
    assert detect_castling(['ke8', 'ra8'], 'e8c8', 'k', 'black') == 'a8d8'


def test_normal_king_move_is_not_castling():
    assert detect_castling(['ke1', 'rh1'], 'e1e2', 'k', 'white') is None


def test_non_king_piece_is_not_castling():
    assert detect_castling(['qe1', 'rh1'], 'e1g1', 'q', 'white') is None


def test_rook_missing_invalidates_castling():
    assert detect_castling(['ke1'], 'e1g1', 'k', 'white') is None


def test_king_not_on_start_square():
    assert detect_castling(['kd1', 'rh1'], 'd1g1', 'k', 'white') is None
