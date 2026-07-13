import pytest
from solvechessdotcom.solution import get_positions, solution_from_pgn

# Real daily puzzle from 2024-10-19; expected moves verified against the
# solution the old browser-automation flow produced for the same puzzle.
PGN_2024_10_19 = (
    '[Result "1-0"]\n'
    '[FEN "1b2r2r/1p5k/p3Q3/2pN4/3p2P1/P4P1p/8/3q1BK1 w - - 0 1"]\n'
    '\n'
    '1. Qf7+ Kh6 2. g5+ Kxg5 3. Qg7+ Kh5 4. Nf6+ Kh4 5. Qg4# 1-0'
)

# Real daily puzzle from 2025-12-25: includes an en passant capture (2... bxa3)
# and a promotion (7. e8=Q)
PGN_RUDOLPH = (
    '[Result "*"]\n'
    '[FEN "6kq/4p3/3pPp1Q/2pP4/1pP5/1P6/P7/K7 w - - 0 1"]\n'
    '\n'
    '1. Qxh8+ Kxh8 2. a4 bxa3 3. b4 cxb4 4. c5 dxc5 5. d6 exd6 6. e7 Kg7 7. e8=Q *'
)


def test_solution_matches_browser_flow_output():
    solution = solution_from_pgn(PGN_2024_10_19)
    expected = {
        'move1': ('e6f7', 'h7h6'),
        'move2': ('g4g5', 'h6g5'),
        'move3': ('f7g7', 'g5h5'),
        'move4': ('d5f6', 'h5h4'),
        'move5': ('g7g4', None),
    }
    assert len(solution) == 5
    for key, (white, black) in expected.items():
        assert solution[key]['white'] == white
        assert solution[key]['black'] == black
    assert solution['move1']['white_piece'] == 'q'
    assert solution['move1']['black_piece'] == 'k'


def test_promotion_and_en_passant():
    solution = solution_from_pgn(PGN_RUDOLPH)
    # 2... bxa3 captures the a4 pawn en passant
    assert solution['move2']['black'] == 'b4a3'
    assert solution['move2']['black_ep_capture'] == 'a4'
    # 7. e8=Q promotes: UCI carries the promotion piece as 5th char
    assert solution['move7']['white'] == 'e7e8q'


def test_black_to_move_puzzle():
    pgn = (
        '[Result "0-1"]\n'
        '[FEN "1k1r3r/1pp1b1p1/1p2p2p/1P2Pn2/2P2K2/2NP1B1P/R2N1P2/2R5 b - - 0 23"]\n'
        '\n'
        '23... g5+ 24. Kg4 h5# 0-1'
    )
    solution = solution_from_pgn(pgn)
    assert solution['move1']['black'] == 'g7g5'
    assert solution['move1']['white'] == 'f4g4'
    assert solution['move2']['black'] == 'h6h5'
    assert solution['move2']['white'] is None


def test_castling_adds_rook_move():
    pgn = (
        '[Result "*"]\n'
        '[FEN "4k3/8/8/8/8/8/8/4K2R w K - 0 1"]\n'
        '\n'
        '1. O-O *'
    )
    solution = solution_from_pgn(pgn)
    assert solution['move1']['white'] == 'e1g1'
    assert solution['move1']['white_castle_move'] == 'h1f1'


def test_pgn_without_moves_raises():
    with pytest.raises(ValueError):
        solution_from_pgn('[Result "*"]\n[FEN "4k3/8/8/8/8/8/8/4K2R w K - 0 1"]\n\n*')


def test_get_positions():
    positions = get_positions('1b2r2r/1p5k/p3Q3/2pN4/3p2P1/P4P1p/8/3q1BK1 w - - 0 1')
    assert sorted(positions['white_position']) == sorted(
        ['Qe6', 'Nd5', 'Pg4', 'Pa3', 'Pf3', 'Bf1', 'Kg1'])
    assert sorted(positions['black_position']) == sorted(
        ['bb8', 're8', 'rh8', 'pb7', 'kh7', 'pa6', 'pc5', 'pd4', 'ph3', 'qd1'])
