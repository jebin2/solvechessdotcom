import os
import shutil
import time
import random
from typing import Tuple, Optional
from lxml import etree
from solvechessdotcom import config, svg_converter
from custom_logger import logger_config

SQUARE_SIZE = 135
TOTAL_SIZE = 945

PIECE_TO_ID = {
    'k': "#king", 'q': "#queen", 'b': "#bishop",
    'n': "#knight", 'r': '#rook', 'p': '#pawn'
}
ID_TO_PIECE = {v: k for k, v in PIECE_TO_ID.items()}
FILE_TO_NUM = {'a': "0", 'b': "1", 'c': "2", 'd': "3",
               'e': '4', 'f': '5', 'g': '6', 'h': '7'}
RANK_TO_NUM = {str(i): str(i - 1) for i in range(1, 9)}


def convert_chess_notation_to_pixels(file: str, rank: str) -> Tuple[int, int]:
    """Convert chess notation (e.g., 'e4') to pixel coordinates."""
    try:
        x = int(FILE_TO_NUM[file]) * SQUARE_SIZE
        y = TOTAL_SIZE - (int(RANK_TO_NUM[rank]) * SQUARE_SIZE)
        return x, y
    except KeyError as e:
        raise ValueError(f"Invalid chess notation: {file}{rank}") from e

def get_piece_details_from_notation(notation: str) -> Tuple[str, int, int]:
    """Extract piece ID and coordinates from chess notation."""
    piece, file, rank = notation[0], notation[1], notation[2]
    piece_id = PIECE_TO_ID.get(piece.lower())
    if not piece_id:
        raise ValueError(f"Invalid piece notation: {piece}")
    x, y = convert_chess_notation_to_pixels(file, rank)
    return piece_id, x, y

def get_piece_from_coordinates(tree: etree._ElementTree, is_white: bool, notation: str) -> Optional[str]:
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    group_id = 'whitepieces' if is_white else 'blackpieces'
    piece_group = root.find(f".//svg:g[@id='{group_id}']", ns)
    if piece_group is not None:
        for child in piece_group:
            if notation in child.get('_id', ''):
                return ID_TO_PIECE.get(child.get('href'))

    logger_config.error(f"none returned: {notation}")
    return None


def _empty_element(element):
    for child in list(element):
        element.remove(child)


def _remove_element_by_id(element, id_val):
    for child in list(element):
        if id_val in child.get('_id', ''):
            logger_config.debug(f"removed {id_val}")
            element.remove(child)


def get_modified_content(is_create, tree, white_notation, black_notation,
                         remove_notation=None, point=None, remove_dest_piece=False):
    logger_config.debug(f"White:: {white_notation}\nBlack:: {black_notation}\nRemove:: {remove_notation}")
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    for side in ['white', 'black']:
        if side == 'white' and white_notation is None:
            continue
        if side == 'black' and black_notation is None:
            continue

        group_id = 'whitepieces' if side == 'white' else 'blackpieces'
        pieces_el = root.find(f".//svg:g[@id='{group_id}']", ns)

        if pieces_el is not None:
            if is_create:
                _empty_element(pieces_el)

            if remove_notation is not None:
                for notation in remove_notation.split(" "):
                    if white_notation is not None or remove_dest_piece:
                        el = root.find(".//svg:g[@id='whitepieces']", ns)
                        if el is not None:
                            _remove_element_by_id(el, notation)
                    if black_notation is not None or remove_dest_piece:
                        el = root.find(".//svg:g[@id='blackpieces']", ns)
                        if el is not None:
                            _remove_element_by_id(el, notation)

            pieces_el = root.find(f".//svg:g[@id='{group_id}']", ns)
            notations = (white_notation if side == 'white' else black_notation).split(" ")
            for notation in notations:
                piece_id, x, y = get_piece_details_from_notation(notation)
                if point is not None:
                    x, y = point
                new_el = etree.Element("use", attrib={
                    'href': piece_id,
                    'x': str(x), 'y': str(y),
                    'width': str(SQUARE_SIZE), 'height': str(SQUARE_SIZE),
                    '_id': notation
                })
                new_el.tail = "\n"
                pieces_el.append(new_el)

    return tree


def _change_color(root):
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    dark_gradient = root.find(".//svg:linearGradient[@id='darkSquareGradient']", ns)
    color = random.choice(config.CHESS_BOARD_COLORS)
    logger_config.debug(f"New stop-color: {color}")
    for stop in dark_gradient.findall("svg:stop", ns):
        style = stop.attrib.get("style")
        stop.set("style", f'{style.split(":")[0]}:{color}')


def create_svg(output_file, chess_board_template, white_notation, black_notation):
    try:
        logger_config.debug(f"File Path:: {chess_board_template}")
        tree = etree.parse(chess_board_template)
        _change_color(tree.getroot())
        tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        tree = get_modified_content(True, etree.parse(output_file), white_notation, black_notation)
        tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        svg_converter.convert_svg_to_jpg(str(output_file), str(output_file).replace(".svg", ".jpg"))
    except Exception as e:
        logger_config.error(f"create_svg: {str(e)}")
        return None
    return output_file


def _points_to_move(from_x, from_y, to_x, to_y, n):
    x_step = (to_x - from_x) / (n - 1)
    y_step = (to_y - from_y) / (n - 1)
    points = [(round(from_x + x_step * i), round(from_y + y_step * i)) for i in range(n)]
    logger_config.debug(f"Moving points: {points}")
    return points


def update_n_create_svg(base_path, is_white_move, file_name, notation_from_to, order):
    try:
        logger_config.debug(f"Move by:: {'White' if is_white_move else 'Black'}\n"
                     f"File:: {file_name}\nNotation:: {notation_from_to}")
        from_x, from_y = convert_chess_notation_to_pixels(notation_from_to[0], notation_from_to[1])
        to_x, to_y = convert_chess_notation_to_pixels(notation_from_to[2], notation_from_to[3])

        notation_on_pawn_top = None
        if len(notation_from_to) > 4 and notation_from_to[4] != "#":
            notation_on_pawn_top = notation_from_to[4]

        points = _points_to_move(from_x, from_y, to_x, to_y, config.FPS)
        count = 0
        remove_notation = notation_from_to[:2] + " " + notation_from_to[2:4]
        tree = etree.parse(file_name)
        piece = get_piece_from_coordinates(tree, is_white_move, notation_from_to[:2])
        add_notation = f'{piece}{notation_from_to[2:4]}'
        output_svg_file = None

        for point in points:
            if (count + 1 == config.FPS) and notation_on_pawn_top:
                add_notation = f'{notation_on_pawn_top}{add_notation[1:]}'
            output_svg_file = f'{base_path}/new_chess_board-update-{order}-{count}.svg'
            tree = etree.parse(file_name)
            tree = get_modified_content(
                False, tree,
                add_notation if is_white_move else None,
                add_notation if not is_white_move else None,
                remove_notation=remove_notation,
                point=point,
                remove_dest_piece=(count + 1 == config.FPS)
            )
            if count == 0:
                root = tree.getroot()
                ns = {'svg': 'http://www.w3.org/2000/svg'}
                g_el = root.find('.//svg:g[@id="current_move"]', ns)
                g_el.set("piece_point", f"{point[0]},{point[1]}")

            tree.write(output_svg_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            svg_converter.convert_svg_to_png(output_svg_file, output_svg_file.replace(".svg", ".png"))
            count += 1

        return output_svg_file

    except Exception as e:
        logger_config.error(f"update_n_create_svg: {str(e)}")
        return None


def make(data) -> Optional[str]:
    try:

        # data = {'chess_board': {'white_position': ['Qe6', 'Nd5', 'Pg4', 'Pa3', 'Pf3', 'Bf1', 'Kg1'], 'black_position': ['bb8', 're8', 'rh8', 'pb7', 'kh7', 'pa6', 'pc5', 'pd4', 'ph3', 'qd1']}, 'solution': {'move1': {'white': 'e6f7', 'black': 'h7h6'}, 'move2': {'white': 'g4g5', 'black': 'h6g5'}, 'move3': {'white': 'f7g7', 'black': 'g5h5'}, 'move4': {'white': 'd5f6', 'black': 'h5h4'}, 'move5': {'white': 'g7g4', 'black': None}}, 'fen': '1b2r2r/1p5k/p3Q3/2pN4/3p2P1/P4P1p/8/3q1BK1 w - - 0 1', 'date': '2024-10-19', 'turn': 'White'}

        # data = {"chess_board": {"white_position": ["Bh6", "Qa4", "Bc4", "Ne4", "Nc3", "Pd3", "Pg3", "Pb2", "Pc2", "Pf2", "Pg2", "Ra1", "Re1", "Kg1"], "black_position": ["ka8", "bc8", "rh8", "pb7", "pf7", "pg7", "pa6", "qc6", "pc5", "ne5", "rh5"]}, "solution": {"move1": {"white": "h5h1", "black": "g1h1"}, "move2": {"white": "c6h6", "black": "h1g1"}, "move3": {"white": "h6h1", "black": None}}, "fen": "k1b4r/1p3pp1/p1q4B/2p1n2r/Q1B1N3/2NP2P1/1PP2PP1/R3R1K1 b - - 0 1", "date": "2024-10-16", "turn": "Black"}

        white_pieces = data["chess_board"]["white_position"]
        black_pieces = data["chess_board"]["black_position"]
        turn = data['turn']

        chess_board = create_svg(
            config.CHESS_BOARD_WITH_PUZZLE_SVG,
            config.CHESS_BOARD_SVG,
            ' '.join(white_pieces),
            ' '.join(black_pieces)
        )

        moves_dir = config.CHESS_MOVES_PATH
        shutil.rmtree(moves_dir, ignore_errors=True)
        time.sleep(1)
        os.makedirs(moves_dir, exist_ok=True)

        order = 0
        for move in data["solution"].values():
            if turn == 'White':
                if move["white"]:
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, True, chess_board, move["white"], order)
                if move.get("white_castle_move"):
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, True, chess_board, move["white_castle_move"], order)
                if move["black"]:
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, False, chess_board, move["black"], order)
                if move.get("black_castle_move"):
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, False, chess_board, move["black_castle_move"], order)
            else:
                if move["black"]:
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, False, chess_board, move["black"], order)
                if move.get("black_castle_move"):
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, False, chess_board, move["black_castle_move"], order)
                if move["white"]:
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, True, chess_board, move["white"], order)
                if move.get("white_castle_move"):
                    order += 1
                    chess_board = update_n_create_svg(moves_dir, True, chess_board, move["white_castle_move"], order)

        return config.BASE_PATH

    except Exception as e:
        logger_config.error(f"Error creating chess board: {str(e)}")
        return None
