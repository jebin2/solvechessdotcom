def detect_castling(position: list, move: str, piece: str, color: str) -> str | None:
    """
    Detects if castling happened, and returns the correct rook move.
    Supports both kingside and queenside castling for white and black.

    Args:
        position: List of pieces in format like ['rd1', 'pb5', 'kc1']
                  (scraped board data stores both sides' pieces lowercase)
        move: King's move, like 'e1c1'
        piece: 'k' (king)
        color: 'white' or 'black'

    Returns:
        Rook move in the format 'a1d1' or 'h1f1' or None if not castling
    """
    # Determine starting and ending square of the king
    start, end = move[:2], move[2:]

    # Castling can only occur from initial square
    if color == 'white' and piece == 'k' and start == 'e1' and end in ['g1', 'c1']:
        if end == 'g1':
            # Kingside castling
            rook_from, rook_to = 'h1', 'f1'
        else:
            # Queenside castling
            rook_from, rook_to = 'a1', 'd1'
    elif color == 'black' and piece == 'k' and start == 'e8' and end in ['g8', 'c8']:
        if end == 'g8':
            rook_from, rook_to = 'h8', 'f8'
        else:
            rook_from, rook_to = 'a8', 'd8'
    else:
        return None  # Not castling

    # Check if the rook is in the correct position
    rook_present = any(p == 'r' + rook_from for p in position)

    if rook_present:
        return f"{rook_from}{rook_to}"
    else:
        return None  # Castling invalid — rook not found
