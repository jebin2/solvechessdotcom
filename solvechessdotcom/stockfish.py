from custom_logger import logger_config
import subprocess
import json
import os

import shutil

def setup_stockfish_path():
    path = shutil.which("stockfish")
    if not path:
        logger_config.info("Stockfish not found. Installing via apt...")
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "stockfish"], check=True)
            path = shutil.which("stockfish") or "/usr/games/stockfish"
        except subprocess.CalledProcessError as e:
            logger_config.error(f"Failed to install Stockfish: {e}")
            path = "/usr/games/stockfish"
    return path

STOCKFISH_PATH = setup_stockfish_path()

def parse_moves(is_white, pv_line):
    """Parse principal variation line into moves dictionary"""
    moves_part = pv_line.split(' pv ')[1].strip()
    moves = moves_part.split()
    
    result = {}
    move_count = 1
    
    for i in range(0, len(moves)-1, 2):
        if i + 1 < len(moves):
            if is_white:
                result[f"move{move_count}"] = {
                    "white": moves[i],
                    "white_piece": '',
                    "black": moves[i+1],
                    "black_piece": ''
                }
            else:
                result[f"move{move_count}"] = {
                    "black": moves[i],
                    "black_piece": '',
                    "white": moves[i+1],
                    "white_piece": ''
                }
            move_count += 1
    
    # Handle last move if it's a single move
    if len(moves) % 2 == 1:
        if is_white:
            result[f"move{move_count}"] = {
                "white": moves[-1],
                "white_piece": '',
                "black": None,
                "black_piece": ''
            }
        else:
            result[f"move{move_count}"] = {
                "black": moves[-1],
                "black_piece": '',
                "white": None,
                "white_piece": ''
            }
    
    return result

def convert_to_algebraic_notation(board_visual):
    white = []
    black = []
    rows = board_visual.strip().split('\n')[1:-1]  # Skip the top and bottom borders
    
    for rank_index, row in enumerate(rows):
        # Get the pieces from each row and their positions
        cell = 0
        for file_index, char in enumerate(row):
            if char.isalpha():  # Check if the character is a piece
                file = chr(ord('a') + cell-1)  # Convert index to file (a-h)
                if ord(char) < ord('a'):
                    white.append(f"{char}{file}{int(row[-1])}")
                else:
                    black.append(f"{char}{file}{int(row[-1])}")
            if char == '|':
                cell += 1

    return {
        "white_position": white,
        "black_position": black
    }

def stockfish_process(is_white, cmd, stockfish_path, is_board_only=False):
    process = subprocess.Popen(
        [stockfish_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
		env={**os.environ, 'PYTHONUNBUFFERED': '1'}
    )
    process.stdin.write(f"{cmd}\n")
    process.stdin.flush()

    board_visual = ''
    moves = ''
    best_move = ''
    while True:
        line = process.stdout.readline().strip()
        if not line:
            continue

        if line.endswith(' currmovenumber 1'):
            best_move = line.split(" ")[4]
            break

        if '+---+' in line or '| 1' in line or '| 2' in line or '| 3' in line or '| 4' in line or '| 5' in line or '| 6' in line or '| 7' in line or '| 8' in line:
            board_visual += f'{line}\n'
        
        if line.startswith("info depth") and "score mate" in line and "pv" in line:
            moves = line

        if line.startswith("bestmove"):
            best_move = line.split(" ")[1]
            if " ponder " not in line:
                best_move += "#"
            break

    process.terminate()
    process.wait()

    if board_visual:
        board_visual = convert_to_algebraic_notation(board_visual)
    if moves:
        moves = parse_moves(is_white, moves)

    logger_config.debug(f"""chess_board: {board_visual}
solution: {moves}""")

    return board_visual, moves, best_move

def get_board(fen, stockfish_path=STOCKFISH_PATH, moves_made=None):
    cmd = f"""position fen {fen} moves {moves_made}
d
go
""" if moves_made else f"""position fen {fen}
d
go
"""
    board_visual, _, _ = stockfish_process(True if ' w ' in fen else False, cmd, stockfish_path, is_board_only=True)
    return board_visual

def process(fen, stockfish_path=STOCKFISH_PATH, moves_made=None):
    
    cmd = f"""position fen {fen} moves {moves_made}
d
go
""" if moves_made else f"""position fen {fen}
d
go
"""
    board_visual, moves, best_move = stockfish_process(True if ' w ' in fen else False, cmd, stockfish_path)
    
    return {
        "chess_board": board_visual,
        "solution": moves,
        "best_move": best_move
    }

if __name__ == "__main__":
    fen = "2k1r2r/1pp4p/p2n2pq/3pB3/1R6/6P1/PPPnQPKN/R7 b - - 0 1"
    result = process(fen, moves_made=None)
    print(result) # strictly no custom logger