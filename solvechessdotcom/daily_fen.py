import requests
import json
import unicodedata
from datetime import datetime, timedelta
import re
from custom_logger import logger_config

def display_width(s):
    """Calculate the display width of a string, accounting for wide chars like emojis."""
    width = 0
    for ch in str(s):
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ('W', 'F'):
            width += 2
        elif unicodedata.category(ch).startswith('So'):
            width += 2
        else:
            width += 1
    return width

def ljust_display(s, width):
    """Left-justify a string to the given display width."""
    s = str(s)
    padding = width - display_width(s)
    return s + ' ' * max(0, padding)

def get_date_range(when=1):
    end = datetime.now()
    start = end - timedelta(days=when)
    
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def fetch_daily_puzzles(when=1):
    start_date, end_date = get_date_range(when)
    logger_config.info(f"Fetching puzzles from {start_date} to {end_date}")
    
    url = f"https://www.chess.com/callback/puzzles/daily?start={start_date}&end={end_date}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.chess.com/puzzles/daily'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        puzzles = response.json()
        
        fen_pattern = r'\[FEN "(.*?)"\]'
        puzzle_list = []
        for puzzle in puzzles:
            pgn_text = puzzle['pgn']
            match = re.search(fen_pattern, pgn_text)
            fen = match.group(1) if match else None
            
            puzzle_list.append({
                'date': puzzle.get('date', ''),
                'fen': fen,
                'title': puzzle.get('title', ''),
                'turn': 'White' if fen and ' w ' in fen else 'Black'
            })
        
        # Keep only the latest 'when' puzzles
        puzzle_list = puzzle_list[-when:]
        print_puzzle_table(puzzle_list)
        return puzzle_list
        
    except Exception as e:
        raise ValueError(f"Error fetching puzzles: {e}")

def print_puzzle_table(puzzles):
    headers = ["Date", "Title", "Turn", "FEN"]

    col_widths = [
        max(display_width(p["date"]) for p in puzzles + [{"date": headers[0]}]),
        max(25, max(display_width(p["title"]) for p in puzzles + [{"title": headers[1]}])),
        max(10, max(display_width(p["turn"]) for p in puzzles + [{"turn": headers[2]}])),
        max(display_width(p["fen"]) for p in puzzles + [{"fen": headers[3]}]),
    ]

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    header_row = (
        "| "
        + " | ".join(ljust_display(h, w) for h, w in zip(headers, col_widths))
        + " |"
    )

    lines = [sep, header_row, sep]
    for p in puzzles:
        row = (
            "| "
            + " | ".join(
                ljust_display(p[k], w)
                for k, w in zip(["date", "title", "turn", "fen"], col_widths)
            )
            + " |"
        )
        lines.append(row)
    lines.append(sep)

    logger_config.info("\n".join(lines))

if __name__ == "__main__":
    fetch_daily_puzzles()
    