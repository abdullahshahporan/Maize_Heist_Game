"""
tactical_blocker.py — Tactical wall-placement decision layer for the A* agent.
Evaluates wall utility: how much a wall hurts the opponent vs. self.
Optimized: uses single BFS pass per player pre-wall, then lightweight
per-cell BFS on raw grid instead of cloning entire game state.
"""

from game.board import CELL_EMPTY, CELL_TEMP_WALL
from game.rules import get_valid_wall_positions
from utils.pathfinding import bfs_all_distances, bfs_distance_from_grid


def evaluate_wall_placements(game_state):
    """
    For each valid wall position, compute wall_utility =
        opponent_path_increase - self_path_penalty.
    Returns list of (wall_pos, utility) sorted descending by utility.
    Respects MAX_WALLS_PER_PLAYER limit via updated get_valid_wall_positions.
    """
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board
    treasures = game_state.treasures

    wall_positions = get_valid_wall_positions(board, player, opponent,
                                              treasures, game_state.temp_walls)

    if not wall_positions or not treasures:
        return []

    # Pre-compute BFS distances from both players (before any wall)
    opp_dists_before = bfs_all_distances(board, opponent.pos)
    self_dists_before = bfs_all_distances(board, player.pos)

    # Get raw grid reference for in-place wall simulation
    grid = board.grid
    rows = board.rows
    cols = board.cols

    results = []
    for wr, wc in wall_positions:
        # Temporarily place wall directly on grid (avoid clone)
        grid[wr][wc] = CELL_TEMP_WALL

        total_opp_increase = 0.0
        total_self_penalty = 0.0

        for t in treasures:
            tp = (t.row, t.col)
            weight = t.value * 0.05  # normalize (value/20)

            d_opp_before = opp_dists_before.get(tp, -1)
            d_self_before = self_dists_before.get(tp, -1)

            # After-wall distances via lightweight raw-grid BFS
            d_opp_after = bfs_distance_from_grid(grid, rows, cols,
                                                  opponent.pos, tp)
            d_self_after = bfs_distance_from_grid(grid, rows, cols,
                                                   player.pos, tp)

            if d_opp_before >= 0:
                if d_opp_after >= 0:
                    total_opp_increase += (d_opp_after - d_opp_before) * weight
                else:
                    # Wall completely blocks opponent from this treasure
                    total_opp_increase += 10.0 * weight

            if d_self_before >= 0:
                if d_self_after >= 0:
                    penalty = d_self_after - d_self_before
                    if penalty > 0:
                        total_self_penalty += penalty * weight
                else:
                    # Blocks self — heavy penalty
                    total_self_penalty += 15.0 * weight

        # Undo wall placement (restore grid)
        grid[wr][wc] = CELL_EMPTY

        utility = total_opp_increase - total_self_penalty
        results.append(((wr, wc), utility))

    # Sort by utility descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results
