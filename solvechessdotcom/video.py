import os
import shutil

from PIL import Image, ImageSequence, ImageFilter, ImageDraw, ImageFont
from moviepy import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from custom_logger import logger_config
from solvechessdotcom import config, utils
from jebin_lib import normalize_loudness


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

    frames_dir = os.path.join(config.TEMP_PATH, 'video_frames')
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)

    move_points = utils.load_move_points(os.path.dirname(file_in_order[0]))

    gif_img = Image.open(config.CHESS_HIGHLIGHT_GIF)
    gif_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(gif_img)]
    gif_len = len(gif_frames)
    gif_w, gif_h = gif_img.size

    chess_audio = (AudioFileClip(config.CHESS_MOVE_SOUND)
                   .subclipped(AUDIO_TRIM_START, AUDIO_TRIM_END)
                   .with_volume_scaled(0.8))

    frame_paths = []
    durations = []
    audio_clips = []
    current_time = 0.0

    for file in file_in_order:
        name = os.path.basename(file)
        if name.endswith('-0.jpg'):
            # Pause on the position and pulse the highlight over the piece about to move
            order = name[:-len('.jpg')].split('-')[-2]
            pos = move_points.get(order, (0, 0))
            paste_pos = (pos[0] + (135 - gif_w) // 2, pos[1] + (135 - gif_h) // 2)
            base_img = Image.open(file).convert("RGB")

            for k in range(int(config.CHESS_HIGHLIGHT_DUR * fps)):
                gif_frame = gif_frames[k % gif_len]
                combined = base_img.copy()
                combined.paste(gif_frame, paste_pos, mask=gif_frame)
                highlight_path = os.path.join(frames_dir, f'highlight-{order}-{k}.jpg')
                combined.save(highlight_path, quality=92)
                frame_paths.append(highlight_path)
                durations.append(1.0 / fps)

            current_time += config.CHESS_HIGHLIGHT_DUR
        else:
            frame_paths.append(file)
            durations.append(config.CHESS_MOVE_DUR / fps)
            current_time += config.CHESS_MOVE_DUR / fps

            if file.endswith(f'-{fps - 1}.jpg') or file == file_in_order[-1]:
                audio_clips.append(chess_audio.with_start(max(0.0, current_time - AUDIO_CLIP_DUR)))

    # Hold final position
    main_duration = current_time + config.CHESS_HIGHLIGHT_DUR
    frame_paths.append(file_in_order[-1])
    durations.append(config.CHESS_HIGHLIGHT_DUR)

    # End credit
    end_credit_audio = AudioFileClip(config.CHESS_END_CREDIT)
    last_portrait = Image.open(file_in_order[-1]).convert("RGB")
    end_credit_frame = _create_end_credit_frame(last_portrait, _format_solution_text(data['solution']))
    end_credit_path = os.path.join(frames_dir, 'end_credit.jpg')
    end_credit_frame.save(end_credit_path)
    frame_paths.append(end_credit_path)
    durations.append(end_credit_audio.duration)
    audio_clips.append(end_credit_audio.with_start(main_duration))

    logger_config.info("Assembling video clips...")
    final_video = ImageSequenceClip(frame_paths, durations=durations)

    bg_music_main = (AudioFileClip(config.CHESS_BG_MUSIC)
                     .subclipped(0, main_duration)
                     .with_volume_scaled(0.5))
    bg_music_end = (AudioFileClip(config.CHESS_BG_MUSIC)
                    .subclipped(main_duration, main_duration + end_credit_audio.duration)
                    .with_volume_scaled(0.2)
                    .with_start(main_duration))

    final_audio = CompositeAudioClip([bg_music_main, bg_music_end] + audio_clips)
    final_video = final_video.with_audio(final_audio)
    final_video.write_videofile(output_video_path, fps=fps, codec='libx264', audio_codec='aac',
                                threads=max(2, (os.cpu_count() or 2) // 2), logger=None)
    normalize_loudness(output_video_path)
