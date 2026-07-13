from solvechessdotcom import stockfish

BOARD_VISUAL = """+---+---+---+---+---+---+---+---+
|   |   |   |   | k |   |   |   | 8
+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   | 7
+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   | 6
+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   | 5
+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   | 4
+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   | 3
+---+---+---+---+---+---+---+---+
| p |   |   |   |   |   |   |   | 2
+---+---+---+---+---+---+---+---+
|   |   |   |   | K |   |   | R | 1
+---+---+---+---+---+---+---+---+
"""


def test_convert_to_algebraic_notation():
    result = stockfish.convert_to_algebraic_notation(BOARD_VISUAL)
    assert result == {
        "white_position": ["Ke1", "Rh1"],
        "black_position": ["ke8", "pa2"],
    }


PV_LINE = ("info depth 245 seldepth 10 multipv 1 score mate 5 nodes 1000 nps 1 "
           "tbhits 0 time 1 pv e6f7 h7h6 g4g5 h6g5 f7g7 g5h5 d5f6 h5h4 g7g4")


def test_parse_moves_white_to_move():
    moves = stockfish.parse_moves(True, PV_LINE)
    assert moves["move1"] == {"white": "e6f7", "white_piece": '', "black": "h7h6", "black_piece": ''}
    assert moves["move5"] == {"white": "g7g4", "white_piece": '', "black": None, "black_piece": ''}


def test_parse_moves_black_to_move():
    moves = stockfish.parse_moves(False, "info depth 1 score mate 2 pv h5h1 g1h1 c6h6")
    assert moves["move1"] == {"black": "h5h1", "black_piece": '', "white": "g1h1", "white_piece": ''}
    assert moves["move2"] == {"black": "c6h6", "black_piece": '', "white": None, "white_piece": ''}
