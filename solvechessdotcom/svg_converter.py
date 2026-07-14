import io

import cairosvg
from lxml import etree
from PIL import Image
from custom_logger import logger_config
from solvechessdotcom import config


def render_svg_bytes(svg_bytes):
    """Rasterize SVG markup at its natural size and return a PIL RGBA image."""
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
    return Image.open(io.BytesIO(png_bytes)).convert('RGBA')


def render_svg_tree(tree):
    """Rasterize an lxml SVG tree and return a PIL RGBA image."""
    return render_svg_bytes(etree.tostring(tree))


def convert_svg_to_jpg(svg_file_path, jpg_file_path, width=None, height=None):
    width = width or config.IMAGE_SIZE[0]
    height = height or config.IMAGE_SIZE[1]
    png_bytes = cairosvg.svg2png(url=str(svg_file_path))
    with Image.open(io.BytesIO(png_bytes)) as img:
        img = img.resize((width, height), Image.LANCZOS)
        img.convert('RGB').save(jpg_file_path, 'JPEG')
    logger_config.debug(f"Saved JPG: {jpg_file_path}")
