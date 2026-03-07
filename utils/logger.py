"""
logger.py — Match result logging to JSON files.
"""

import os
import json
from datetime import datetime
from config import LOG_DIR


def save_match_log(game_state, ai_times: dict = None):
    """
    Write a JSON log of the completed match.
    ai_times: dict like {1: [list of decision times], 2: [...]}
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    winner_name = game_state.winner.name if game_state.winner else "Draw"

    # Compute average AI decision times
    avg_times = {}
    if ai_times:
        for pid, times in ai_times.items():
            if times:
                avg_times[f"player_{pid}_avg_time"] = round(
                    sum(times) / len(times), 4
                )

    record = {
        "timestamp": datetime.now().isoformat(),
        "game_mode": game_state.game_mode,
        "difficulty": game_state.difficulty,
        "winner": winner_name,
        "end_reason": game_state.end_reason,
        "player1_score": game_state.player1.score,
        "player2_score": game_state.player2.score,
        "total_turns": game_state.turn_count,
        "total_rounds": game_state.round_count,
        "player1_treasures": game_state.player1.collected_count,
        "player2_treasures": game_state.player2.collected_count,
        "player1_walls_placed": game_state.wall_placements.get(1, 0),
        "player2_walls_placed": game_state.wall_placements.get(2, 0),
        **avg_times,
    }

    filename = datetime.now().strftime("match_%Y%m%d_%H%M%S.json")
    filepath = os.path.join(LOG_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return filepath
