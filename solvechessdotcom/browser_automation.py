from custom_logger import logger_config
from . import stockfish
import json
from . import common
import copy
from browser_manager import BrowserManager
from browser_manager.browser_config import BrowserConfig

def click(page, name, timeout=1000 * 60 * 2, delay=4000, seconds=8):
	logger_config.debug(f"Checking availability for {name}")
	page.wait_for_selector(name, timeout=timeout)
	element = page.query_selector(name)
	if element:
		logger_config.debug(f"Element found {name}")
		page.hover(name, force=True)
		page.click(name, delay=delay, force=True)
		logger_config.debug(f"Clicked {name}")
		logger_config.debug("Waiting after clicked", seconds=seconds)
	else:
		raise ValueError(f'Element {name} does not exists.')

def char_to_number(char):
	if 'a' <= char <= 'z':  # Ensure it's a lowercase letter
		return ord(char) - ord('a') + 1
	else:
		raise ValueError("Input must be a lowercase letter")

def get_chess_board_details(page, id="board-board"):
	return page.evaluate("""
		(() => {
			var board = document.getElementById('""" + id + """');
			var rect = board.getBoundingClientRect();
			var pieces = board.querySelectorAll('.piece');
			var position = {'width': rect.width, 'height': rect.height, 'white': [], 'black': []};

			pieces.forEach(piece => {
				var classArr = piece.classList;
				var squareClass;
				if (classArr[0] && classArr[0].includes("square")) {
					squareClass = classArr[0];
				} else if (classArr[1] && classArr[1].includes("square")) {
					squareClass = classArr[1];
				} else if (classArr[2] && classArr[2].includes("square")) {
					squareClass = classArr[2];
				}
				if (squareClass && classArr[2] && squareClass.includes('-')) {
					var pieceClass;
					if (classArr[0].startsWith("w") || classArr[0].startsWith("b")) {
						pieceClass = classArr[0];
					} else if (classArr[1].startsWith("w") || classArr[1].startsWith("b")) {
						pieceClass = classArr[1];
					} else if (classArr[2].startsWith("w") || classArr[2].startsWith("b")) {
						pieceClass = classArr[2];
					}
					var pos = squareClass.split('-')[1];
					var x = String.fromCharCode(96 + Number(pos.substring(0, 1)));
					var y = pos.substring(1);
					var pieceType = pieceClass.substr(1);

					if (pieceClass.startsWith('w')) {
						position.white.push(pieceType + x + y);
					} else if (pieceClass.startsWith('b')) {
						position.black.push(pieceType + x + y);
					}
				}
			});

			if (board.querySelectorAll('.highlight')[0]) {
				var high1 = board.querySelectorAll('.highlight')[0].classList;
				if (high1[0].includes("square")) {
					high1 = high1[0];
				} else if (high1[1].includes("square")) {
					high1 = high1[1];
				}
				var pos1 = high1.split('-')[1];
				var x1 = String.fromCharCode(96 + Number(pos1.substring(0, 1)));
				var y1 = pos1.substring(1);
				var high2 = board.querySelectorAll('.highlight')[1].classList;
				if (high2[0].includes("square")) {
					high2 = high2[0];
				} else if (high2[1].includes("square")) {
					high2 = high2[1];
				}
				var pos2 = high2.split('-')[1];
				var x2 = String.fromCharCode(96 + Number(pos2.substring(0, 1)));
				var y2 = pos2.substring(1);
				if (board.querySelectorAll('.' + high1).length > 1) {
					position['system_move'] = x2 + y2 + x1 + y1;
				} else {
					position['system_move'] = x1 + y1 + x2 + y2;
				}
				var piece = position.white.filter(x => x.endsWith(position['system_move'].substring(2, 4)))[0];
				if (piece) {
					position['system_move_piece'] = piece[0];
				} else {
					piece = position.black.filter(x => x.endsWith(position['system_move'].substring(2, 4)))[0];
					if (piece) {
						position['system_move_piece'] = piece[0];
					}
				}
			}

			return position;
		})();
	""")

def get_system_move_and_piece(page, prev_chess_data, is_white_turn):
	try:
		logger_config.debug("Determining system move based on previous and current positions.")
		chess_data = get_chess_board_details(page)
		if not chess_data:
			return None

		current_piece = ''
		if is_white_turn:
			current_piece = [piece for piece in prev_chess_data['black'] if chess_data['system_move'][0:2] in piece][0][0]
		else:
			current_piece = [piece for piece in prev_chess_data['white'] if chess_data['system_move'][0:2] in piece][0][0]

		if current_piece != chess_data["system_move_piece"]:
			chess_data["system_move"] = f'{chess_data["system_move"]}{chess_data["system_move_piece"]}'

		logger_config.debug(f"System move determined: {chess_data['system_move']}")
		return chess_data["system_move"], chess_data["system_move_piece"]
	except Exception as e:
		raise ValueError(f"Error determining system move: {e}")

def move_piece(page, move):
	logger_config.info("Wait before move", seconds=2)
	piece_class = f".square-{char_to_number(move[0])}{move[1]}"
	logger_config.info(f"Clicking:: {piece_class}")
	click(page, piece_class)

	piece_class = f".square-{char_to_number(move[2])}{move[3]}"
	page.wait_for_selector(piece_class, timeout=8000)
	logger_config.info(f"Clicking:: {piece_class}")
	click(page, piece_class)

def select_piece(page, new_piece_class):
	page.wait_for_selector(new_piece_class, timeout=8000)
	logger_config.info(f"Clicking:: {new_piece_class}")
	click(page, new_piece_class)

def play_chess(fen):
	solution = {}
	config = BrowserConfig()
	config.docker_name = "solvechessdotcom"
	with BrowserManager(config) as page:
		page.goto("https://www.chess.com/daily-chess-puzzle")
		page.wait_for_function("""
			() => {
				const board = document.getElementById("board-board");
				return board && board.querySelectorAll(".piece").length > 0;
			}
		""")
		page.wait_for_timeout(8000)

		# Dismiss "Update browser" popup and any other blocking overlays
		page.evaluate("""
			(() => {
				// Close any "update browser" or notification banners
				document.querySelectorAll('[class*="banner"] button, [class*="modal"] button[class*="close"], [class*="dismiss"], [class*="notification"] button, [aria-label="Close"]').forEach(el => {
					try { el.click(); } catch(e) {}
				});
				// Remove any overlay/modal blocking elements
				document.querySelectorAll('[class*="upgrade-banner"], [class*="update-banner"], [class*="browser-banner"]').forEach(el => {
					try { el.remove(); } catch(e) {}
				});
			})()
		""")
		page.wait_for_timeout(2000)

		element = page.query_selector('.cc-button-component.cc-button-primary.cc-button-xx-large.cc-button-full')
		if element:
			click(page, ".cc-button-component.cc-button-primary.cc-button-xx-large.cc-button-full")

		element = page.query_selector('.cc-button-component.cc-button-primary.cc-button-large')
		if element:
			logger_config.info("Wait before reload...", seconds=2)
			click(page, ".cc-button-component.cc-button-primary.cc-button-large")

		is_white_turn = True if ' w ' in fen else False
		side = "white" if is_white_turn else "black"
		other_side = "black" if is_white_turn else "white"
		moves_made = ''

		moves_exceed = 0
		while True:
			chess_data = get_chess_board_details(page)
			system_move = ""
			system_move_piece = ""
			moves_exceed += 1
			data = stockfish.process(fen, moves_made=moves_made)
			best_move = data['best_move']
			logger_config.debug(f"Next best move: {best_move}")
			new_piece = best_move[4] if len(best_move) > 4 else None
			new_piece = None if new_piece == "#" else new_piece
			new_piece_class = None

			current_piece = ''
			if is_white_turn:
				current_piece = [piece for piece in chess_data['white'] if best_move[0:2] in piece][0][0]
				new_piece_class = f".promotion-piece.w{new_piece}" if new_piece else None
			else:
				current_piece = [piece for piece in chess_data['black'] if best_move[0:2] in piece][0][0]
				new_piece_class = f".promotion-piece.b{new_piece}" if new_piece else None

			logger_config.info(f"current_piece:: {current_piece}")
			logger_config.info(f"new_piece_class:: {new_piece_class}")
			move_piece(page, best_move)
			if new_piece_class:
				select_piece(page, new_piece_class)

			user_castle_move = detect_castling(chess_data[side], best_move, current_piece, side)
			logger_config.info(f"User Castle move:: {user_castle_move}")

			logger_config.info("Waiting for solved transistion", seconds=4)
			element = page.query_selector('.message-move-move.message-move-solved')
			if element or moves_exceed > 20:
				if is_white_turn:
					solution[f"move{moves_exceed}"] = {
						"white": data['best_move'],
						"white_piece": current_piece,
						"black": '',
						"black_piece": ''
					}
					if user_castle_move:
						solution[f"move{moves_exceed}"][f"white_castle_move"] = user_castle_move
				else:
					solution[f"move{moves_exceed}"] = {
						"black": data['best_move'],
						"black_piece": current_piece,
						"white": '',
						"white_piece": ''
					}
					if user_castle_move:
						solution[f"move{moves_exceed}"][f"black_castle_move"] = user_castle_move
				logger_config.info("Puzzle solved or maximum move limit reached.")
				break
			else:
				logger_config.warning("Not solved yet.")

			system_move, system_move_piece = get_system_move_and_piece(page, chess_data, is_white_turn)
			system_castle_move = detect_castling(chess_data[other_side], best_move, current_piece, side)
			logger_config.info(f"System Castle move:: {system_castle_move}")

			moves_made += f" {best_move} {system_move}"

			if is_white_turn:
				solution[f"move{moves_exceed}"] = {
					"white": data['best_move'],
					"white_piece": current_piece,
					"black": system_move,
					"black_piece": system_move_piece
				}
				if user_castle_move:
					solution[f"move{moves_exceed}"][f"white_castle_move"] = user_castle_move
				if system_castle_move:
					solution[f"move{moves_exceed}"][f"white_castle_move"] = system_castle_move
			else:
				solution[f"move{moves_exceed}"] = {
					"black": data['best_move'],
					"black_piece": current_piece,
					"white": system_move,
					"white_piece": system_move_piece
				}
				if user_castle_move:
					solution[f"move{moves_exceed}"][f"black_castle_move"] = user_castle_move
				if system_castle_move:
					solution[f"move{moves_exceed}"][f"black_castle_move"] = system_castle_move

		return solution

def is_end_reached(page):
	return page.evaluate("""
		(() => {
			var total_moves = document.querySelectorAll('div[data-whole-move-number]').length;
			return total_moves;
		})();
	""")

import copy

def get_castle_move(prev_chess_data, chess_data, whose_turn="white"):
	cloned_prev = copy.deepcopy(prev_chess_data[whose_turn])
	cloned_new = copy.deepcopy(chess_data[whose_turn])

	if len(chess_data["system_move"]) == 4:
		move = chess_data["system_move"]
		piece = chess_data["system_move_piece"]

		if piece.lower() == 'k':
			# King move
			king_start = f"{piece}{move[0:2]}"
			king_end = f"{piece}{move[2:]}"
			
			for lst in (cloned_prev, cloned_new):
				if king_start in lst:
					lst.remove(king_start)
				if king_end in lst:
					lst.remove(king_end)

			all_items = [item for item in cloned_prev]

			for item in all_items:
				if item in cloned_new:
					cloned_prev.remove(item)
					cloned_new.remove(item)

			# Get rook movement from the difference
			rook_start = next((item[1:] for item in cloned_prev if item[0].lower() == 'r'), None)
			rook_end = next((item[1:] for item in cloned_new if item[0].lower() == 'r'), None)

			if rook_start and rook_end:
				return f"{rook_start}{rook_end}"

	return None

def detect_castling(position: list, move: str, piece: str, color: str) -> str | None:
    """
    Detects if castling happened, and returns the correct rook move.
    Supports both kingside and queenside castling for white and black.

    Args:
        position: List of pieces in format like ['rd1', 'pb5', 'kc1']
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
    rook_symbol = 'r' if color == 'white' else 'R'
    rook_present = any(p == rook_symbol + rook_from for p in position)

    if rook_present:
        return f"{rook_from}{rook_to}"
    else:
        return None  # Castling invalid — rook not found

CLOSE_SOURCE_DIALOG = "upload-dialog .close mat-icon"
SOURCE_ITEM_MORE = ".source-item-more-button"
SOURCE_REMOVE = ".cdk-overlay-container .mdc-button__label"
SOURCE_DELETE = ".cdk-overlay-container .submit"
COPIED_TEXT = "upload-dialog .chip-groups div:nth-child(3) mat-chip span:nth-child(2) span span span:nth-child(1)"
PASTE_COPIED_TEXT = "upload-dialog textarea"
PASTE_COPIED_TEXT_SAVE = "upload-dialog paste-text form button"
CUSTOMIZE = "audio-overview .action-container-buttons div button"
CUSTOMIZE_AUDIO_TEXT = "producer-audio-dialog textarea"
GENERATE = "mat-dialog-actions button"
DOWNLOAD_MENU = "audio-player button:nth-child(4) mat-icon"
AUDIO_DOWNLOAD = ".cdk-overlay-container a .mat-mdc-menu-item-text"
AUDIO_LOAD = "audio-overview .mdc-button__label"
AUDIO_DELETE = ".cdk-overlay-container .delete-button .mat-mdc-menu-item-text"
AUDIO_DELETE_CONFIRM = ".cdk-overlay-container mat-dialog-actions button:nth-child(2)"

def delete_source_data(page):
	try:
		click(page, SOURCE_ITEM_MORE, timeout=5000)
		click(page, SOURCE_REMOVE, timeout=5000)
		click(page, SOURCE_DELETE, timeout=5000)
	except:
		pass

def delete_audio(page):
	try:
		click(page, AUDIO_LOAD, timeout=5000)
		click(page, DOWNLOAD_MENU, timeout=5000)
		click(page, AUDIO_DELETE, timeout=5000)
		click(page, AUDIO_DELETE_CONFIRM, timeout=5000)
	except:
		pass

def delete_old_data(page):
	element = page.query_selector(CLOSE_SOURCE_DIALOG)
	if element:
		return True

	delete_source_data(page)
	delete_audio(page)
	page.reload()
	page.wait_for_load_state("domcontentloaded")
	logger_config.info("Wait for page Load", seconds=4)
