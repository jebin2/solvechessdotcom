# solvechessdotcom

Automated pipeline that turns the [chess.com daily puzzle](https://www.chess.com/puzzles/daily) into a rendered solution video (1080x1920 portrait, YouTube Shorts format) ready for publishing.

## How it works

`main.py` runs `ChessPipeline` in a loop (every 60s, or once with `--onepass`):

1. **Fetch** (`daily_fen.py`) — pulls the daily puzzle (date, FEN, title) from the chess.com callback API.
2. **Solve** (`browser_automation.py` + `stockfish.py`) — opens the puzzle in a browser (via `browser_manager`), asks Stockfish for the best move, plays it on the page, and records the site's replies until solved.
3. **Render frames** (`board.py`) — builds an SVG board for the position, then for each half-move rasterizes the board twice (piece lifted / piece landed) plus the moving piece as a transparent sprite, and composites the animation frames in PIL.
4. **Assemble video** (`video.py`) — highlight pulse on the piece about to move, move animations, move sounds, background music, and a blurred end-credit card with the solution.

Output and publish metadata land in `content_to_be_processed/chess/<date>/` (`progress.json` + `<date>.mp4`); a separate publisher app picks them up from there. `progress.json` doubles as a resume checkpoint, and a pid lockfile in `/tmp` prevents concurrent runs on the same puzzle.

## Requirements

- Python >= 3.10 (production runs in the `solvechessdotcom_env` pyenv env)
- [Stockfish](https://stockfishchess.org/): `sudo apt-get install -y stockfish`
- ffmpeg (for moviepy)
- Docker (for the `browser_manager` browser container)

```bash
pip install .
```

## Running

```bash
bash run_app.sh             # kill previous instance, set CPU affinity, loop forever
bash run_app.sh --onepass   # single pass
bash run_pipelines.sh       # supervisor loop around run_app.sh --onepass
```

## Tests

```bash
python -m pytest
```

## Configuration

Paths, board colors, FPS, animation durations, and YouTube publish defaults live in `solvechessdotcom/config.py`. Generated intermediates go to `temp/` (wiped each run).
