import numpy as np
from PIL import Image, ImageSequence, ImageFilter, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
from custom_logger import logger_config
from solvechessdotcom import config, utils
from jebin_lib import normalize_loudness


def _to_portrait(img):
    """Crop centre 1080-wide strip from landscape image and pad to 1080×1920."""
    w, h = img.size
    x_start = (w - 1080) // 2
    cropped = img.crop((x_start, 0, x_start + 1080, h))
    canvas = Image.new("RGB", (1080, 1920), "black")
    canvas.paste(cropped, (0, (1920 - h) // 2))
    return canvas


def _format_solution_text(solution):
    lines = []
    for i, move_details in enumerate(solution.values(), 1):
        parts = []
        for key in ['white', 'black', 'white_castle_move', 'black_castle_move']:
            m = move_details.get(key)
            if m:
                parts.append(f"{m[:2]}-{m[2:4]}")
        if parts:
            lines.append(f"{i}.  {'     '.join(parts)}")
    return '\n'.join(lines)


def _create_end_credit_frame(base_portrait, solution_text):
    blurred = base_portrait.filter(ImageFilter.GaussianBlur(radius=20))
    draw = ImageDraw.Draw(blurred)
    font = ImageFont.truetype(config.CHESS_FONT, size=70)
    W, H = blurred.size
    bbox = draw.multiline_textbbox((0, 0), solution_text, font=font, align='center')
    x = (W - (bbox[2] - bbox[0])) / 2
    y = (H - (bbox[3] - bbox[1])) / 2
    draw.multiline_text(
        (x, y), solution_text,
        font=font, fill=(108, 92, 231),
        stroke_width=6, stroke_fill=(0, 0, 0),
        align='center'
    )
    return blurred


def render(file_in_order, data, output_video_path):
    fps = config.FPS
    AUDIO_TRIM_START = 0.455
    AUDIO_TRIM_END = 0.608
    AUDIO_CLIP_DUR = AUDIO_TRIM_END - AUDIO_TRIM_START

    gif_img = Image.open(config.CHESS_HIGHLIGHT_GIF)
    gif_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(gif_img)]
    gif_len = len(gif_frames)
    gif_w, gif_h = gif_img.size

    chess_audio = (AudioFileClip(config.CHESS_MOVE_SOUND)
                   .subclipped(AUDIO_TRIM_START, AUDIO_TRIM_END)
                   .with_volume_scaled(0.8))

    video_clips = []
    audio_clips = []
    current_time = 0.0

    for file in file_in_order:
        if file.endswith('-0.png') and '-highlight-' not in file:
            svg_path = file.replace('.png', '.svg')
            pos = utils.chess_position(svg_path)
            offset_x = (135 - gif_w) // 2
            offset_y = (135 - gif_h) // 2
            paste_pos = (pos[0] + offset_x, pos[1] + offset_y)
            base_img = Image.open(file).convert("RGBA")

            frames_to_generate = int(config.CHESS_HIGHLIGHT_DUR * fps)
            for k in range(frames_to_generate):
                gif_frame = gif_frames[k % gif_len]
                combined = base_img.copy()
                combined.paste(gif_frame, paste_pos, mask=gif_frame)
                portrait = _to_portrait(combined.convert("RGB"))
                video_clips.append(ImageClip(np.array(portrait)).with_duration(1.0 / fps))

            current_time += config.CHESS_HIGHLIGHT_DUR
        else:
            portrait = _to_portrait(Image.open(file).convert("RGB"))
            video_clips.append(ImageClip(np.array(portrait)).with_duration(config.CHESS_MOVE_DUR / fps))
            current_time += config.CHESS_MOVE_DUR / fps

            if file.endswith(f'-{fps - 1}.png') or file == file_in_order[-1]:
                audio_clips.append(chess_audio.with_start(current_time - AUDIO_CLIP_DUR))

    # Hold final position
    main_duration = current_time + config.CHESS_HIGHLIGHT_DUR
    last_portrait = _to_portrait(Image.open(file_in_order[-1]).convert("RGB"))
    video_clips.append(ImageClip(np.array(last_portrait)).with_duration(config.CHESS_HIGHLIGHT_DUR))

    # End credit
    end_credit_audio = AudioFileClip(config.CHESS_END_CREDIT)
    end_credit_frame = _create_end_credit_frame(last_portrait, _format_solution_text(data['solution']))
    video_clips.append(ImageClip(np.array(end_credit_frame)).with_duration(end_credit_audio.duration))
    audio_clips.append(end_credit_audio.with_start(main_duration))

    logger_config.info("Assembling video clips...")
    final_video = concatenate_videoclips(video_clips)

    bg_music_main = (AudioFileClip(config.CHESS_BG_MUSIC)
                     .subclipped(0, main_duration)
                     .with_volume_scaled(0.5))
    bg_music_end = (AudioFileClip(config.CHESS_BG_MUSIC)
                    .subclipped(main_duration, main_duration + end_credit_audio.duration)
                    .with_volume_scaled(0.2)
                    .with_start(main_duration))

    final_audio = CompositeAudioClip([bg_music_main, bg_music_end] + audio_clips)
    final_video = final_video.with_audio(final_audio)
    final_video.write_videofile(output_video_path, fps=fps, codec='libx264', audio_codec='aac', logger=None)
    normalize_loudness(output_video_path)
