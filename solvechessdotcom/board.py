import copy
import os
import shutil
import random
from typing import Tuple, Optional
from lxml import etree
from solvechessdotcom import config, svg_converter, utils
from custom_logger import logger_config

SVG_NS = 'http://www.w3.org/2000/svg'
NS = {'svg': SVG_NS}

SQUARE_SIZE = 135
TOTAL_SIZE = 945
# Transparent margin around the piece sprite so stroke/glow are not clipped
SPRITE_PAD = 30

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
    group_id = 'whitepieces' if is_white else 'blackpieces'
    piece_group = root.find(f".//svg:g[@id='{group_id}']", NS)
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

    for side in ['white', 'black']:
        if side == 'white' and white_notation is None:
            continue
        if side == 'black' and black_notation is None:
            continue

        group_id = 'whitepieces' if side == 'white' else 'blackpieces'
        pieces_el = root.find(f".//svg:g[@id='{group_id}']", NS)

        if pieces_el is not None:
            if is_create:
                _empty_element(pieces_el)

            if remove_notation is not None:
                for notation in remove_notation.split(" "):
                    if white_notation is not None or remove_dest_piece:
                        el = root.find(".//svg:g[@id='whitepieces']", NS)
                        if el is not None:
                            _remove_element_by_id(el, notation)
                    if black_notation is not None or remove_dest_piece:
                        el = root.find(".//svg:g[@id='blackpieces']", NS)
                        if el is not None:
                            _remove_element_by_id(el, notation)

            pieces_el = root.find(f".//svg:g[@id='{group_id}']", NS)
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
    dark_gradient = root.find(".//svg:linearGradient[@id='darkSquareGradient']", NS)
    color = random.choice(config.CHESS_BOARD_COLORS)
    logger_config.debug(f"New stop-color: {color}")
    for stop in dark_gradient.findall("svg:stop", NS):
        style = stop.attrib.get("style")
        stop.set("style", f'{style.split(":")[0]}:{color}')


def create_svg(output_file, chess_board_template, white_notation, black_notation):
    logger_config.debug(f"File Path:: {chess_board_template}")
    tree = etree.parse(chess_board_template)
    _change_color(tree.getroot())
    tree = get_modified_content(True, tree, white_notation, black_notation)
    tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    svg_converter.convert_svg_to_jpg(str(output_file), str(output_file).replace(".svg", ".jpg"))
    return output_file


def _points_to_move(from_x, from_y, to_x, to_y, n):
    x_step = (to_x - from_x) / (n - 1)
    y_step = (to_y - from_y) / (n - 1)
    points = [(round(from_x + x_step * i), round(from_y + y_step * i)) for i in range(n)]
    logger_config.debug(f"Moving points: {points}")
    return points


def _render_piece_sprite(tree, group_id, piece_id):
    """Rasterize a single piece (with the board's gradients/stroke/glow) on a
    transparent canvas of SQUARE_SIZE plus SPRITE_PAD margin on each side."""
    root = tree.getroot()
    size = SQUARE_SIZE + 2 * SPRITE_PAD
    sprite_svg = etree.Element(f'{{{SVG_NS}}}svg', nsmap={None: SVG_NS})
    sprite_svg.set('viewBox', f'{-SPRITE_PAD} {-SPRITE_PAD} {size} {size}')
    sprite_svg.set('width', str(size))
    sprite_svg.set('height', str(size))

    for defs in root.iter(f'{{{SVG_NS}}}defs'):
        sprite_svg.append(copy.deepcopy(defs))

    src_group = root.find(f".//svg:g[@id='{group_id}']", NS)
    g = etree.SubElement(sprite_svg, f'{{{SVG_NS}}}g')
    for attr, val in src_group.attrib.items():
        if attr != 'id':
            g.set(attr, val)
    etree.SubElement(g, f'{{{SVG_NS}}}use', attrib={
        'href': piece_id, 'x': '0', 'y': '0',
        'width': str(SQUARE_SIZE), 'height': str(SQUARE_SIZE),
    })
    return svg_converter.render_svg_bytes(etree.tostring(sprite_svg))


def update_n_create_svg(base_path, is_white_move, file_name, notation_from_to, order):
    """Generate the animation frames for one half-move.

    Rasterizes the board twice (piece lifted / piece landed) and the moving
    piece once as a transparent sprite, then composites the in-between frames
    in PIL. Returns the new position SVG path and the move's start pixel
    position (portrait coordinates, for the highlight overlay).
    """
    logger_config.debug(f"Move by:: {'White' if is_white_move else 'Black'}\n"
                 f"File:: {file_name}\nNotation:: {notation_from_to}")
    from_x, from_y = convert_chess_notation_to_pixels(notation_from_to[0], notation_from_to[1])
    to_x, to_y = convert_chess_notation_to_pixels(notation_from_to[2], notation_from_to[3])

    promotion_piece = None
    if len(notation_from_to) > 4 and notation_from_to[4] != "#":
        promotion_piece = notation_from_to[4]

    remove_notation = notation_from_to[:2] + " " + notation_from_to[2:4]
    group_id = 'whitepieces' if is_white_move else 'blackpieces'

    position_tree = etree.parse(file_name)
    piece = get_piece_from_coordinates(position_tree, is_white_move, notation_from_to[:2])
    if piece is None:
        raise ValueError(f"No piece found at {notation_from_to[:2]} for move {notation_from_to}")
    final_piece = promotion_piece if promotion_piece else piece
    final_notation = f'{final_piece}{notation_from_to[2:4]}'

    # Background: the position with the moving piece lifted off the board
    # (a captured enemy piece stays visible until the final frame)
    bg_tree = etree.parse(file_name)
    bg_group = bg_tree.getroot().find(f".//svg:g[@id='{group_id}']", NS)
    for notation in remove_notation.split(" "):
        _remove_element_by_id(bg_group, notation)
    background = utils.to_portrait(svg_converter.render_svg_tree(bg_tree).convert("RGB"))

    sprite = _render_piece_sprite(position_tree, group_id, PIECE_TO_ID[piece])

    # Final position: piece landed (promotion applied), captured piece removed
    final_tree = get_modified_content(
        False, etree.parse(file_name),
        final_notation if is_white_move else None,
        final_notation if not is_white_move else None,
        remove_notation=remove_notation,
        point=(to_x, to_y),
        remove_dest_piece=True,
    )
    output_svg_file = f'{base_path}/new_chess_board-update-{order}-{config.FPS - 1}.svg'
    final_tree.write(output_svg_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    points = _points_to_move(from_x, from_y, to_x, to_y, config.FPS)
    for count, point in enumerate(points[:-1]):
        frame = background.copy()
        paste_pos = (point[0] - SPRITE_PAD, point[1] + utils.PORTRAIT_Y_PAD - SPRITE_PAD)
        frame.paste(sprite, paste_pos, mask=sprite)
        frame.save(f'{base_path}/new_chess_board-update-{order}-{count}.jpg', quality=92)

    final_frame = utils.to_portrait(svg_converter.render_svg_tree(final_tree).convert("RGB"))
    final_frame.save(f'{base_path}/new_chess_board-update-{order}-{config.FPS - 1}.jpg', quality=92)

    start_point = (points[0][0], points[0][1] + utils.PORTRAIT_Y_PAD)
    return output_svg_file, start_point


def make(data):
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
    os.makedirs(moves_dir, exist_ok=True)

    sides = ('white', 'black') if turn == 'White' else ('black', 'white')
    move_points = {}
    order = 0
    for move in data["solution"].values():
        for side in sides:
            for key in (side, f"{side}_castle_move"):
                notation = move.get(key)
                if notation:
                    order += 1
                    chess_board, start_point = update_n_create_svg(
                        moves_dir, side == 'white', chess_board, notation, order)
                    move_points[order] = start_point

    utils.save_move_points(moves_dir, move_points)
