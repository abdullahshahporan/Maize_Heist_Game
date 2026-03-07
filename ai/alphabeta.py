"""
alphabeta.py — Minimax with Alpha-Beta pruning search.
Optimized: move ordering, transposition table, fast cutoffs.
"""

from game.actions import ACTION_MOVE
from ai.heuristics import evaluate

# Transposition table: keyed by (p1_pos, p2_pos, current_idx, turn_count)
# Stores (depth, flag, value) — flag: 0 = exact, 1 = lower, 2 = upper
_tt = {}
_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_TT_MAX_SIZE = 100000


def clear_transposition_table():
    """Clear the TT between top-level searches."""
    _tt.clear()


def _tt_key(game_state):
    """Fast hash key from mutable game state."""
    gs = game_state
    return (gs.player1.row, gs.player1.col, gs.player1.score,
            gs.player2.row, gs.player2.col, gs.player2.score,
            gs.current_player_index, gs.turn_count)


def _order_actions(actions, game_state):
    """Order actions for better alpha-beta pruning.
    Priority: moves onto treasures > other moves > wall placements.
    This dramatically increases cutoff rate."""
    treasure_set = set()
    for t in game_state.treasures:
        treasure_set.add((t.row, t.col))

    capture_moves = []
    regular_moves = []
    wall_actions = []

    for action in actions:
        if action.action_type == ACTION_MOVE:
            if action.target in treasure_set:
                capture_moves.append(action)
            else:
                regular_moves.append(action)
        else:
            wall_actions.append(action)

    # Captures first, then regular moves, then walls
    return capture_moves + regular_moves + wall_actions


def alphabeta(game_state, depth: int, alpha: float, beta: float,
              maximizing: bool, maximizing_player_id: int) -> float:
    """
    Minimax search with alpha-beta pruning, move ordering, and
    transposition table for efficient search.
    """
    # Leaf node
    if depth == 0 or game_state.game_over:
        return evaluate(game_state, maximizing_player_id)

    # Transposition table lookup
    key = _tt_key(game_state)
    tt_entry = _tt.get(key)
    if tt_entry is not None:
        tt_depth, tt_flag, tt_value = tt_entry
        if tt_depth >= depth:
            if tt_flag == _TT_EXACT:
                return tt_value
            elif tt_flag == _TT_LOWER:
                alpha = max(alpha, tt_value)
            elif tt_flag == _TT_UPPER:
                beta = min(beta, tt_value)
            if alpha >= beta:
                return tt_value

    actions = game_state.get_all_actions()

    if not actions:
        return evaluate(game_state, maximizing_player_id)

    # Order moves for better pruning
    actions = _order_actions(actions, game_state)

    orig_alpha = alpha

    if maximizing:
        value = float('-inf')
        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            score = alphabeta(child, depth - 1, alpha, beta,
                              False, maximizing_player_id)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break  # beta cutoff
    else:
        value = float('inf')
        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            score = alphabeta(child, depth - 1, alpha, beta,
                              True, maximizing_player_id)
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                break  # alpha cutoff

    # Store in transposition table
    if len(_tt) < _TT_MAX_SIZE:
        if value <= orig_alpha:
            flag = _TT_UPPER
        elif value >= beta:
            flag = _TT_LOWER
        else:
            flag = _TT_EXACT
        _tt[key] = (depth, flag, value)

    return value
