import json
import os
from PIL import Image

PORTRAIT_SIZE = (1080, 1920)
# The 1080px-tall board render is vertically centred on the portrait canvas
PORTRAIT_Y_PAD = (PORTRAIT_SIZE[1] - 1080) // 2

MOVE_POINTS_FILE = "move_points.json"


def to_portrait(img):
    """Crop the centre 1080-wide strip from a landscape image and pad to 1080x1920."""
    w, h = img.size
    x_start = (w - PORTRAIT_SIZE[0]) // 2
    cropped = img.crop((x_start, 0, x_start + PORTRAIT_SIZE[0], h))
    canvas = Image.new("RGB", PORTRAIT_SIZE, "black")
    canvas.paste(cropped, (0, (PORTRAIT_SIZE[1] - h) // 2))
    return canvas


def save_move_points(moves_dir, points):
    """Persist per-move start pixel positions (portrait coords), keyed by move order."""
    with open(os.path.join(moves_dir, MOVE_POINTS_FILE), 'w') as f:
        json.dump({str(k): list(v) for k, v in points.items()}, f)


def load_move_points(moves_dir):
    with open(os.path.join(moves_dir, MOVE_POINTS_FILE)) as f:
        return {k: tuple(v) for k, v in json.load(f).items()}
