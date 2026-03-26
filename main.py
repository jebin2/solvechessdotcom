from jebin_lib import load_env, utils, ensure_hf_mounted, sync_to_hf, sync_from_hf
load_env()

import sys
import hashlib
import json
import os
import shutil
import tempfile
import traceback

from custom_logger import logger_config
from solvechessdotcom import board, browser_automation, config, daily_fen, stockfish, video

class ChessPipeline:

    def __init__(self):
        ensure_hf_mounted(config.HF_BUCKET_ID, config.HF_TOKEN, config.HF_MOUNT_PATH)
        self.data = None
        self.file_in_order = []

    @property
    def repo_main_path(self):
        return f"chess/{self.data['date']}"

    @property
    def final_video_repo_path(self):
        return f"{self.repo_main_path}/{self.data['date']}.mp4"

    @property
    def lock_path(self):
        key = hashlib.md5(self.dest_dir.encode()).hexdigest()
        return os.path.join(tempfile.gettempdir(), f"solvechessdotcom_{key}.lock")

    def _acquire_lock(self) -> bool:
        try:
            with open(self.lock_path, 'x') as f:
                f.write(str(os.getpid()))
            return True
        except FileExistsError:
            try:
                with open(self.lock_path) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return False
            except (ProcessLookupError, ValueError, OSError):
                os.remove(self.lock_path)
                return self._acquire_lock()

    def _release_lock(self):
        try:
            os.remove(self.lock_path)
        except FileNotFoundError:
            pass

    @property
    def dest_dir(self):
        path = os.path.join(config.CONTENT_TO_BE_PROCESSED, self.repo_main_path)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def progress_file(self):
        return os.path.join(self.dest_dir, "progress.json")

    @property
    def output_video(self):
        return os.path.join(self.dest_dir, f"{self.data['date']}.mp4")

    def get_latest_processed_date(self):
        try:
            from datetime import date
            today = str(date.today())
            progress_path = os.path.join(config.CONTENT_TO_BE_PROCESSED, "chess", today, "progress.json")
            if os.path.exists(progress_path):
                with open(progress_path) as f:
                    progress = json.load(f)
                if progress.get("PROCESSED", False) and progress.get("FINAL_VIDEO_PATH"):
                    return today
        except Exception:
            pass
        return "1970-01-01"

    def fetch_puzzle(self):
        try:
            self.data = daily_fen.fetch_daily_puzzles()[0]
        except Exception as e:
            logger_config.error(f"Failed to fetch puzzle: {e}")
            return False

        if self.data['date'] == self.get_latest_processed_date():
            logger_config.info(f"Puzzle for {self.data['date']} already completed. Skipping.")
            return False

        if utils.is_valid_json(self.progress_file):
            with open(self.progress_file) as f:
                progress = json.load(f)
            if self.data['date'] == progress['date']:
                self.data = progress

        logger_config.info(f"Puzzle: {json.dumps(self.data, indent=4)}")
        return True

    def solve(self):
        if not self.data.get('solution'):
            self.data['solution'] = browser_automation.play_chess(self.data['fen'])
        self.data['chess_board'] = stockfish.get_board(self.data['fen'])
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=4)
        logger_config.info(f"Chess Puzzle With Solution: {json.dumps(self.data, indent=4)}")

    def generate_frames(self):
        board.make(self.data)
        logger_config.debug("Getting Chess move files...")
        files = utils.list_files_recursive(config.CHESS_MOVES_PATH)
        filtered = [f for f in files if f.endswith('.png') and 'new_chess_board-update-' in f]

        def sort_key(filename):
            parts = filename.split('/')[-1].replace('.png', '').split('-')
            return int(parts[-2]), int(parts[-1])

        self.file_in_order = sorted(filtered, key=sort_key)
        logger_config.success(f"Found {len(self.file_in_order)} frames.")

    def render_video(self):
        output_path = self.output_video
        logger_config.info(f"Generating video to {output_path}...")
        video.render(self.file_in_order, self.data, output_path)

        with open(self.progress_file, 'r') as f:
            data = json.load(f)

        data['FINAL_VIDEO_PATH'] = self.final_video_repo_path
        data['PROCESSED'] = True

        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=4)

        logger_config.success(f"Video generated successfully: {output_path}")


    def reset_temp(self):
        shutil.rmtree(config.TEMP_PATH, ignore_errors=True)
        os.makedirs(config.TEMP_PATH, exist_ok=True)
        logger_config.info("Temp directory reset.")

    def run(self):
        if self.fetch_puzzle():
            if not self._acquire_lock():
                logger_config.warning(f"Folder locked by another process, skipping: {self.dest_dir}")
                return
            try:
                sync_to_hf(config.CONTENT_TO_BE_PROCESSED, config.HF_MOUNT_PATH, subpath=self.repo_main_path)
                self.reset_temp()
                self.solve()
                self.generate_frames()
                self.render_video()
            finally:
                self._release_lock()


if __name__ == '__main__':
    if '--syncfromhf' in sys.argv:
        sync_from_hf(config.CONTENT_TO_BE_PROCESSED, config.HF_BUCKET_ID, config.HF_TOKEN)
        sys.exit(0)

    while True:
        try:
            ChessPipeline().run()
            logger_config.info("Completed processing")
        except Exception as e:
            logger_config.error(f"Failed to process: {e}")
            logger_config.error(traceback.format_exc())

        logger_config.info("Sleeping for 60 seconds", seconds=60)
