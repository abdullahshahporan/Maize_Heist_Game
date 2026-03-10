"""
tactical_blocker.py — Backward-compatible re-exports from wall_logic.py.

All wall evaluation logic now lives in ai.wall_logic.
This module re-exports the public API for existing imports.
"""

from ai.wall_logic import (
    chokepoint_score,
    opponent_cutoff_bonus,
    race_impact,
    score_treasure_importance,
    shortlist_wall_positions,
    evaluate_wall_placements,
)
