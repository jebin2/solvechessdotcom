from jebin_lib import load_env, utils
load_env()

import json
import os

from custom_logger import logger_config
from solvechessdotcom import board, browser_automation, common, config, daily_fen, stockfish, video


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
            with open("progress.json") as f:
                progress = json.load(f)

            if progress.get("FINAL_VIDEO_PATH"):
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

        if utils.is_valid_json('progress.json'):
            with open('progress.json') as f:
                progress = json.load(f)
            if self.data['date'] == progress['date']:
                self.data = progress

        logger_config.info(f"Puzzle: {json.dumps(self.data, indent=4)}")
        return True

    def solve(self):
        if not self.data.get('solution'):
            self.data['solution'] = browser_automation.play_chess(self.data['fen'])
        self.data['chess_board'] = stockfish.get_board(self.data['fen'])
        self.data['CREDENTIAL_NAME'] = config.CHESS_CRED_NAME
        self.data['TOKEN_NAME'] = config.CHESS_TOKEN_NAME
        with open('progress.json', 'w') as f:
            json.dump(self.data, f, indent=4)
        logger_config.info(f"Chess Puzzle With Solution: {json.dumps(self.data, indent=4)}")

    def generate_frames(self):
        board.make(self.data)
        logger_config.debug("Getting Chess move files...")
        files = common.list_files_recursive(config.CHESS_MOVES_PATH)
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

        with open('progress.json', 'r') as f:
            data = json.load(f)

        data['FINAL_VIDEO_PATH'] = self.final_video_repo_path

        with open('progress.json', 'w') as f:
            json.dump(data, f, indent=4)

        logger_config.success(f"Video generated successfully: {output_path}")

    def upload_video(self):
        try:
            from jebin_lib import HFDatasetClient
            client = HFDatasetClient(repo_id=config.PUBLISH_HF_REPO_ID)

            client.upload(config.CHESS_OUTPUT_VIDEO, self.final_video_repo_path)
            client.upload(os.path.join(config.BASE_PATH, 'progress.json'), f"{self.repo_main_path}/progress.json")

        except Exception as e:
            logger_config.error(f"Failed to publish: {e}")

    def run(self):
        if self.fetch_puzzle():
            self.solve()
            self.generate_frames()
            self.render_video()
            self.upload_video()


if __name__ == '__main__':
    ChessPipeline().run()
