"""
minimax_agent.py — Minimax + Alpha-Beta driver with difficulty-tuned aggression.

Design:
- Smart instant-capture scaled by value and opponent threat
- Wall pre-filtering: Easy only places walls with proven impact (≥8 utility);
  Medium requires moderate impact (≥3.5); Hard considers any positive utility
- Urgency: searches deeper when behind or in critical positions
- Tighter aspiration windows for faster convergence
- Iterative deepening with TT reuse across depths
"""

from config import DIFFICULTY_SETTINGS
from game.actions import ACTION_MOVE, ACTION_PLACE_WALL
from ai.alphabeta import alphabeta, clear_transposition_table, _order_actions
from ai.wall_logic import evaluate_wall_placements
from utils.pathfinding import bfs_all_distances

ASPIRATION_BASE = 15.0

# Minimum wall utility required before Minimax considers placing a wall.
# Easy: any wall that meaningfully delays opponent; Hard: almost any block.
_WALL_UTIL_THRESHOLD = {'easy': 1.5, 'medium': 0.8, 'hard': 0.2}


def _opponent_threat(game_state):
    """Check if opponent is 1-2 steps from a high-value treasure."""
    opp = game_state.get_opponent()
    board = game_state.board
    opp_dists = bfs_all_distances(board, opp.pos)
    max_threat = 0
    for t in game_state.treasures:
        d = opp_dists.get(t.pos, 999)
        if d <= 2:
            max_threat = max(max_threat, t.value)
    return max_threat


def _filter_walls_by_utility(actions, game_state, difficulty):
    """Pre-filter wall actions using BFS wall evaluation.

    Removes blindfolded walls (ones that don't meaningfully hinder the
    opponent) so the search focuses on moves and impactful blocks only.
    """
    threshold = _WALL_UTIL_THRESHOLD.get(difficulty, 3.5)

    move_actions = [a for a in actions if a.action_type == ACTION_MOVE]
    wall_actions = [a for a in actions if a.action_type == ACTION_PLACE_WALL]

    if not wall_actions:
        return actions

    # Evaluate all candidate walls once with BFS
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board
    my_dists = bfs_all_distances(board, player.pos)
    opp_dists = bfs_all_distances(board, opponent.pos)

    wall_eval = evaluate_wall_placements(
        game_state,
        self_dists_before=my_dists,
        opp_dists_before=opp_dists,
        max_candidates=8,
    )
    good_walls = {pos for pos, util in wall_eval if util >= threshold}

    filtered_walls = [a for a in wall_actions if a.target in good_walls]

    # Always keep move actions; only keep walls that clear the threshold
    return move_actions + filtered_walls


def choose_action_minimax(game_state, difficulty):
    depth = DIFFICULTY_SETTINGS[difficulty]["minimax_depth"]
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    actions = game_state.get_all_actions()

    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]

    # ── Urgency: search deeper when behind or critical ──
    score_diff = player.score - opponent.score
    if score_diff < -15:
        depth = min(depth + 2, 7)
    elif score_diff < -5:
        depth = min(depth + 1, 6)

    n_treasures = len(game_state.treasures)
    if len(actions) <= 3 or n_treasures <= 3:
        depth = min(depth + 1, 7)
    elif n_treasures <= 6:
        depth = min(depth + 1, 6)

    treasure_values = game_state.get_treasure_value_map()
    best_capture = None
    best_capture_val = 0
    for action in actions:
        if action.action_type == ACTION_MOVE:
            value = treasure_values.get(action.target, 0)
            if value > best_capture_val:
                best_capture_val = value
                best_capture = action

    # ── Smart instant-capture ────────────────────────────
    # Diamonds: always grab immediately.
    # Gold: grab unless opponent is threatening a bigger prize.
    # Cash (5 pts): grab only when A* is NOT about to collect a diamond —
    #   if A* is 1-2 steps from a diamond, search instead (may prefer blocking).
    if best_capture:
        if best_capture_val >= 20:
            return best_capture
        if best_capture_val >= 10:
            opp_threat = _opponent_threat(game_state)
            if opp_threat <= best_capture_val:
                return best_capture
            # opp_threat > gold: fall through to search (may prefer blocking)
        elif best_capture_val >= 5:   # cash only (< 10)
            opp_threat = _opponent_threat(game_state)
            if opp_threat < 15:          # no diamond threat — safe to grab cash
                return best_capture
            # A* threatening a diamond: let search decide (block vs grab cash)

    # ── Difficulty-based wall pre-filtering ──────────────
    # Removes walls that don't meet the minimum BFS-utility threshold.
    # This prevents Easy/Medium Minimax from placing blind walls that
    # do nothing meaningful but still lock down A*'s movement.
    actions = _filter_walls_by_utility(actions, game_state, difficulty)

    if not actions:
        # Fallback: all moves (should not happen if the board has moves)
        actions = game_state.get_all_actions()

    if len(actions) == 1:
        return actions[0]

    actions = _order_actions(actions, game_state)
    clear_transposition_table()

    root_children = []
    for action in actions:
        child = game_state.clone()
        child.apply_action(action)
        root_children.append((action, child))

    best_action = actions[0]
    prev_value = 0.0

    for current_depth in range(1, depth + 1):
        if current_depth >= 2:
            window = ASPIRATION_BASE + current_depth * 2.0
            alpha = prev_value - window
            beta = prev_value + window
        else:
            alpha = float("-inf")
            beta = float("inf")

        current_best_action = actions[0]
        current_best_value = float("-inf")

        for action, child in root_children:
            value = alphabeta(child, current_depth - 1, alpha, beta, False, player.id)
            if value > current_best_value:
                current_best_value = value
                current_best_action = action

        if current_best_value <= alpha or current_best_value >= beta:
            current_best_value = float("-inf")
            for action, child in root_children:
                value = alphabeta(child, current_depth - 1, float("-inf"), float("inf"), False, player.id)
                if value > current_best_value:
                    current_best_value = value
                    current_best_action = action

        best_action = current_best_action
        prev_value = current_best_value

        if best_action != root_children[0][0]:
            for index, (action, child) in enumerate(root_children):
                if action == best_action:
                    root_children.insert(0, root_children.pop(index))
                    break

        if current_best_value >= 9000.0:
            break

    return best_action
