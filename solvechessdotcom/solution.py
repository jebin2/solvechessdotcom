"""Derive the puzzle solution and board positions from the chess.com PGN.

The daily-puzzle API returns the full solution as PGN movetext; parsing it
with python-chess replaces the old browser-automation + Stockfish flow.
"""
import io

import chess
import chess.pgn


def get_positions(fen):
    """Piece placements for board rendering: white like 'Qe6', black like 'bb8'."""
    board = chess.Board(fen)
    white, black = [], []
    for square, piece in board.piece_map().items():
        entry = f"{piece.symbol()}{chess.square_name(square)}"
        (white if piece.color == chess.WHITE else black).append(entry)
    return {"white_position": white, "black_position": black}


def _castle_rook_move(board, move):
    if board.is_kingside_castling(move):
        return 'h1f1' if board.turn == chess.WHITE else 'h8f8'
    if board.is_queenside_castling(move):
        return 'a1d1' if board.turn == chess.WHITE else 'a8d8'
    return None


def _ep_captured_square(move):
    return chess.square_name(chess.square(
        chess.square_file(move.to_square), chess.square_rank(move.from_square)))


def solution_from_pgn(pgn_text):
    """Parse PGN movetext into the solution dict the renderer expects.

    Moves are UCI coordinates ('e6f7', promotions like 'e7e8q'). Castling
    adds '{side}_castle_move' with the rook move; en passant adds
    '{side}_ep_capture' with the captured pawn's square.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("Could not parse PGN")

    board = game.board()
    moves = list(game.mainline_moves())
    if not moves:
        raise ValueError("PGN contains no solution moves")

    solution = {}
    first_turn = board.turn
    move_num = 0
    for move in moves:
        side = 'white' if board.turn == chess.WHITE else 'black'
        if board.turn == first_turn:
            move_num += 1
            solution[f"move{move_num}"] = {
                "white": None, "white_piece": '',
                "black": None, "black_piece": '',
            }
        entry = solution[f"move{move_num}"]
        entry[side] = move.uci()
        entry[f"{side}_piece"] = board.piece_at(move.from_square).symbol().lower()

        castle_rook = _castle_rook_move(board, move)
        if castle_rook:
            entry[f"{side}_castle_move"] = castle_rook
        if board.is_en_passant(move):
            entry[f"{side}_ep_capture"] = _ep_captured_square(move)

        board.push(move)

    return solution
