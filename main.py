from jebin_lib import load_env, utils
load_env()

import json
import os
import shutil
import traceback

from custom_logger import logger_config
from solvechessdotcom import board, browser_automation, config, daily_fen, stockfish, video
from jebin_lib import HFBucketClient

class ChessPipeline:

    def __init__(self):
        self.data = None
        self.file_in_order = []

    @property
    def repo_main_path(self):
        return f"chess/{self.data['date']}"

    @property
    def final_video_repo_path(self):
        return f"{self.repo_main_path}/{self.data['date']}.mp4"

    def get_latest_processed_date(self):
        try:
            with open(config.PROGRESS_FILE) as f:
                progress = json.load(f)

            if progress.get("PROCESSED", False) and progress.get("FINAL_VIDEO_PATH"):
                return progress.get("date", "1970-01-01")

            return "1970-01-01"

        except Exception:
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

        if utils.is_valid_json(config.PROGRESS_FILE):
            with open(config.PROGRESS_FILE) as f:
                progress = json.load(f)
            if self.data['date'] == progress['date']:
                self.data = progress

        logger_config.info(f"Puzzle: {json.dumps(self.data, indent=4)}")
        return True

    def solve(self):
        if not self.data.get('solution'):
            self.data['solution'] = browser_automation.play_chess(self.data['fen'])
        self.data['chess_board'] = stockfish.get_board(self.data['fen'])
        with open(config.PROGRESS_FILE, 'w') as f:
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
        output_path = config.CHESS_OUTPUT_VIDEO
        logger_config.info(f"Generating video to {output_path}...")
        video.render(self.file_in_order, self.data, output_path)

        with open(config.PROGRESS_FILE, 'r') as f:
            data = json.load(f)

        data['FINAL_VIDEO_PATH'] = self.final_video_repo_path
        data['PROCESSED'] = True

        with open(config.PROGRESS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        logger_config.success(f"Video generated successfully: {output_path}")

    def upload_video(self):
        try:
            hf_client = HFBucketClient(bucket_id=config.HF_BUCKET_ID) if config.HF_BUCKET_ID else None

            if hf_client:
                upload_dir = os.path.join(config.TEMP_PATH, 'upload')
                os.makedirs(upload_dir, exist_ok=True)
                os.rename(config.CHESS_OUTPUT_VIDEO, os.path.join(upload_dir, f"{self.data['date']}.mp4"))
                shutil.copy(config.PROGRESS_FILE, os.path.join(upload_dir, 'progress.json'))
                hf_client.upload_folder(upload_dir, self.repo_main_path)

        except Exception as e:
            logger_config.error(f"Failed to publish: {e}")

    def reset_temp(self):
        shutil.rmtree(config.TEMP_PATH, ignore_errors=True)
        os.makedirs(config.TEMP_PATH, exist_ok=True)
        logger_config.info("Temp directory reset.")

    def run(self):
        if self.fetch_puzzle():
            self.reset_temp()
            self.solve()
            self.generate_frames()
            self.render_video()
            self.upload_video()


if __name__ == '__main__':
    while True:
        try:
            ChessPipeline().run()
            logger_config.info("Completed processing")
        except Exception as e:
            logger_config.error(f"Failed to process: {e}")
            logger_config.error(traceback.format_exc())

        logger_config.info("Sleeping for 60 seconds", seconds=60)
