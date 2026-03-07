"""
astar_agent.py — AI Agent 2: A* pathfinding + Tactical Wall Placement.

Decision flow:
1. Choose best treasure target (single BFS from each player).
2. Compute shortest A* path to that treasure.
3. Estimate opponent path to competing treasures.
4. Evaluate nearby valid wall placements via tactical layer.
5. Calculate wall benefit (utility).
6. Compare best move vs best wall.
7. Choose action.

Optimized: uses single BFS flood-fill per player for all treasure distance
lookups, avoids redundant valid-move recomputation.
"""

from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from game.rules import get_valid_moves
from utils.pathfinding import astar, bfs_all_distances
from ai.tactical_blocker import evaluate_wall_placements

# Utility threshold: wall must be this useful to prefer it over moving
WALL_UTILITY_THRESHOLD = 1.5


def _choose_best_treasure(game_state, my_dists: dict, opp_dists: dict):
    """
    Pick the treasure with the best value/distance ratio for the current
    player, considering opponent competition.
    Uses pre-computed BFS distance maps (no redundant pathfinding).
    """
    treasures = game_state.treasures
    if not treasures:
        return None

    best_score = float('-inf')
    best_treasure = None

    for t in treasures:
        tp = (t.row, t.col)
        d_self = my_dists.get(tp, -1)
        d_opp = opp_dists.get(tp, -1)

        if d_self < 0:
            continue  # unreachable

        race_bonus = 0
        if d_opp >= 0:
            race_bonus = (d_opp - d_self) * 2

        score = t.value / (d_self + 1) + race_bonus

        if score > best_score:
            best_score = score
            best_treasure = t

    return best_treasure


def choose_action_astar(game_state) -> Action:
    """
    Main decision function for the A* + tactical agent.
    Returns the chosen Action.
    """
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board

    # Single BFS from each player — reused for treasure targeting
    my_dists = bfs_all_distances(board, player.pos)
    opp_dists = bfs_all_distances(board, opponent.pos)

    # ── 1. Determine best treasure target ───────────────
    target_treasure = _choose_best_treasure(game_state, my_dists, opp_dists)

    # Pre-compute valid moves once
    valid_moves = get_valid_moves(board, player, opponent)

    # ── 2. Compute A* path to target ────────────────────
    best_move_action = None
    if target_treasure:
        blocked = {opponent.pos}
        path = astar(board, player.pos, target_treasure.pos, blocked)
        if path and len(path) > 1:
            next_cell = path[1]
            if next_cell in valid_moves:
                best_move_action = Action(ACTION_MOVE, next_cell)

    # If no path to treasure, pick the valid move closest to target
    if best_move_action is None and valid_moves:
        if target_treasure:
            tr, tc = target_treasure.row, target_treasure.col
            valid_moves.sort(key=lambda m: abs(m[0] - tr) + abs(m[1] - tc))
        best_move_action = Action(ACTION_MOVE, valid_moves[0])

    # ── 3-5. Evaluate wall placements ──────────────────
    wall_options = evaluate_wall_placements(game_state)

    best_wall_action = None
    best_wall_utility = float('-inf')
    if wall_options:
        best_wall_pos, best_wall_utility = wall_options[0]
        best_wall_action = Action(ACTION_PLACE_WALL, best_wall_pos)

    # ── 6-7. Compare move vs wall ──────────────────────
    if (best_wall_action
            and best_wall_utility > WALL_UTILITY_THRESHOLD
            and best_move_action):
        return best_wall_action

    if best_move_action:
        return best_move_action

    if best_wall_action:
        return best_wall_action

    # Absolute fallback
    actions = game_state.get_all_actions()
    return actions[0] if actions else None

    best_wall_action = None
    best_wall_utility = float('-inf')
    if wall_options:
        best_wall_pos, best_wall_utility = wall_options[0]
        best_wall_action = Action(ACTION_PLACE_WALL, best_wall_pos)

    # ── 6-7. Compare move vs wall ──────────────────────
    if (best_wall_action
            and best_wall_utility > WALL_UTILITY_THRESHOLD
            and best_move_action):
        return best_wall_action

    if best_move_action:
        return best_move_action

    # Fallback: wall or nothing
    if best_wall_action:
        return best_wall_action

    # Absolute fallback — should not happen if rules are consistent
    actions = game_state.get_all_actions()
    return actions[0] if actions else None
