from jebin_lib import load_env
load_env()

import json
import os

from custom_logger import logger_config
from solvechessdotcom import board, browser_automation, common, config, daily_fen, stockfish, video


class ChessPipeline:

    def __init__(self):
        self.data = None
        self.file_in_order = []

    def fetch_puzzle(self):
        self.data = daily_fen.fetch_daily_puzzles()[0]
        try:
            with open('progress.json') as f:
                progress = json.load(f)
            if self.data['date'] == progress['date']:
                self.data = progress
        except Exception:
            pass
        logger_config.info(f"Puzzle: {json.dumps(self.data, indent=4)}")

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
        output_path = os.path.join(config.CHESS_MOVES_PATH, 'output.mp4')
        logger_config.info(f"Generating video to {output_path}...")
        video.render(self.file_in_order, self.data, output_path)
        logger_config.success(f"Video generated successfully: {output_path}")

    def publish(self):
        try:
            from jebin_lib import HFDatasetClient

            # upload video
            output_path = os.path.join(config.CHESS_MOVES_PATH, 'output.mp4')
            repo_path = "chess/output.mp4"
            HFDatasetClient(repo_id=config.PUBLISH_HF_REPO_ID).upload(output_path, repo_path)

            # upload json
            json_path = os.path.join(config.BASE_PATH, 'progress.json')
            repo_path = "chess/progress.json"
            HFDatasetClient(repo_id=config.PUBLISH_HF_REPO_ID).upload(json_path, repo_path)

        except Exception as e:
            logger_config.error(f"Failed to publish: {e}")

    def run(self):
        self.fetch_puzzle()
        self.solve()
        self.generate_frames()
        self.render_video()
        self.publish()


if __name__ == '__main__':
    ChessPipeline().run()
