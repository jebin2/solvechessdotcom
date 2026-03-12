import os
import platform

_arch = platform.machine()
_pkg_dir = os.path.dirname(__file__)

BASE_PATH = os.path.dirname(_pkg_dir)

TEMP_PATH = os.path.join(BASE_PATH, 'temp')
os.makedirs(TEMP_PATH, exist_ok=True)

HF_BUCKET_ID = os.getenv("HF_BUCKET_ID")

CHESS_BOARD_SVG = os.path.join(_pkg_dir, 'assets/images', 'new_chess_board.svg')
CHESS_BOARD_WITH_PUZZLE_SVG = os.path.join(_pkg_dir, 'assets/images', 'chess_board_with_puzzle.svg')
CHESS_BOARD_WITH_PUZZLE_JPG = os.path.join(_pkg_dir, 'assets/images', 'chess_board_with_puzzle.jpg')
CHESS_MOVES_PATH = os.path.join(TEMP_PATH, 'moves')
CHESS_OUTPUT_VIDEO = os.path.join(TEMP_PATH, 'output.mp4')

CHESS_HIGHLIGHT_GIF = os.path.join(_pkg_dir, 'assets/images', 'chess_highlight.gif')

CHESS_FONT = os.path.join(_pkg_dir, 'assets/fonts', 'font_1.ttf')

CHESS_END_CREDIT = os.path.join(_pkg_dir, 'assets/audio', 'chess_end_credits_puzzle.wav')

CHESS_MOVE_SOUND = os.path.join(_pkg_dir, 'assets/audio', 'main_chess_move.mp3')

CHESS_BG_MUSIC = os.path.join(_pkg_dir, 'assets/audio', 'Lazy River Dream.mp3')

TEMP_OUTPUT = os.path.join(BASE_PATH, 'temp')

CHESS_BOARD_COLORS = ["#2751c7", "#309771", "#9146bff2", "#c52b79e67", "#5a6df3", "#E94057"]

FPS = 24
IMAGE_SIZE = (1920, 1080)
CHESS_MOVE_DUR=0.5
CHESS_HIGHLIGHT_DUR=1