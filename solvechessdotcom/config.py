import os
import platform

_arch = platform.machine()
_pkg_dir = os.path.dirname(__file__)

BASE_PATH = os.path.dirname(_pkg_dir)

TEMP_PATH = os.path.join(BASE_PATH, 'temp')
os.makedirs(TEMP_PATH, exist_ok=True)


CONTENT_TO_BE_PROCESSED = os.path.join(BASE_PATH, 'content_to_be_processed')
os.makedirs(CONTENT_TO_BE_PROCESSED, exist_ok=True)

CHESS_BOARD_SVG = os.path.join(_pkg_dir, 'assets/images', 'new_chess_board.svg')
# Generated per run; kept out of the package assets directory
CHESS_BOARD_WITH_PUZZLE_SVG = os.path.join(TEMP_PATH, 'chess_board_with_puzzle.svg')

CHESS_MOVES_PATH = os.path.join(TEMP_PATH, 'moves')

CHESS_HIGHLIGHT_GIF = os.path.join(_pkg_dir, 'assets/images', 'chess_highlight.gif')

CHESS_FONT = os.path.join(_pkg_dir, 'assets/fonts', 'font_1.ttf')

CHESS_END_CREDIT = os.path.join(_pkg_dir, 'assets/audio', 'chess_end_credits_puzzle.wav')

CHESS_MOVE_SOUND = os.path.join(_pkg_dir, 'assets/audio', 'main_chess_move.mp3')

CHESS_BG_MUSIC = os.path.join(_pkg_dir, 'assets/audio', 'Lazy River Dream.mp3')

CHESS_BOARD_COLORS = ["#2751c7", "#309771", "#9146bf", "#c52b79", "#5a6df3", "#E94057"]

FPS = 24
IMAGE_SIZE = (1920, 1080)
CHESS_MOVE_DUR=0.5
CHESS_HIGHLIGHT_DUR=1

PUBLISH_DEFAULTS = {
    'NEXT_ALLOWED_PUBLISH_DATETIME': None,  # publish immediately
    'PUBLISH_IN_YT': True,
    'PUBLISH_IN_TWITTER': False,
    'YT_CREDENTIAL_FILE': "ytcredentials.json",
    'YT_TOKEN_FILE': "yttoken.json",
    'YT_DESCRIPTION': "#chess #chessbreakdown #chessshorts",
    'YT_TAGS': ['ChessBreakdown', 'ChessAnalysis', 'ChessReview', 'recap', 'shorts'],
    'TWITTER_CREDENTIAL_FILE': None,
    'TWITTER_TOKEN_FILE': None,
}
YOUTUBE_TITLE_TEMPLATE = "How to solve Chess.com today's daily puzzle : {date}  #ChessPuzzles #ChessTactics #challenges"