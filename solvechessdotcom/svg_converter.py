import cairosvg
from custom_logger import logger_config
import os
import uuid
from PIL import Image
from solvechessdotcom import config

def _tmp_png():
    os.makedirs(config.TEMP_OUTPUT, exist_ok=True)
    return os.path.join(config.TEMP_OUTPUT, f"{uuid.uuid4().hex}.png")


def convert_svg_to_jpg(svg_file_path, jpg_file_path,
                       width=None, height=None):
    width = width or config.IMAGE_SIZE[0]
    height = height or config.IMAGE_SIZE[1]
    try:
        png_path = _tmp_png()
        cairosvg.svg2png(url=svg_file_path, write_to=png_path)
        with Image.open(png_path) as img:
            img = img.resize((width, height), Image.LANCZOS)
            img.convert('RGB').save(jpg_file_path, 'JPEG')
        os.remove(png_path)
        logger_config.debug(f"Saved JPG: {jpg_file_path}")
    except Exception as e:
        logger_config.error(f"Error in convert_svg_to_jpg: {e}")


def convert_svg_to_png(svg_file_path, png_file_path):
    try:
        cairosvg.svg2png(url=svg_file_path, write_to=png_file_path)
        logger_config.debug(f"Saved PNG: {png_file_path}")
    except Exception as e:
        logger_config.error(f"Error in convert_svg_to_png: {e}")
