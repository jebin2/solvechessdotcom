from PIL import Image
from solvechessdotcom import utils


def test_to_portrait_dimensions():
    landscape = Image.new("RGB", (1920, 1080), "red")
    portrait = utils.to_portrait(landscape)
    assert portrait.size == (1080, 1920)
    # Board strip is vertically centred, black bars above and below
    assert portrait.getpixel((540, 960)) == (255, 0, 0)
    assert portrait.getpixel((540, 10)) == (0, 0, 0)
    assert portrait.getpixel((540, 1910)) == (0, 0, 0)


def test_move_points_roundtrip(tmp_path):
    points = {1: (540, 690), 2: (0, 1365)}
    utils.save_move_points(str(tmp_path), points)
    loaded = utils.load_move_points(str(tmp_path))
    assert loaded == {'1': (540, 690), '2': (0, 1365)}
