"""
alphabeta.py — Minimax with Alpha-Beta pruning search.
Optimized: fast TT key, lightweight move ordering, wall-pruning
at depth > 2 to cut branching factor, aspiration windows.
"""

from game.actions import ACTION_MOVE, ACTION_PLACE_WALL
from ai.heuristics import evaluate

# Transposition table
_tt = {}
_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_TT_MAX_SIZE = 200000


def clear_transposition_table():
    _tt.clear()


def _tt_key(game_state):
    """Fast hash key.  Uses a compact tuple built once per node.

    Treasure and temp-wall identity is encoded via a hash of the
    board grid rows that contain them, which is much cheaper than
    sorting full tuples every call."""
    gs = game_state
    # Board grid signature — hash of the per-row tuples.  This captures
    # both permanent and temp-wall layout without sorting.
    grid_sig = hash(tuple(tuple(row) for row in gs.board.grid))
    return (
        gs.player1.row, gs.player1.col, gs.player1.score,
        gs.player2.row, gs.player2.col, gs.player2.score,
        gs.current_player_index, gs.turn_count,
        len(gs.treasures), grid_sig,
    )


def _order_actions(actions, game_state):
    """Lightweight move ordering — avoids per-action treasure dict.

    Bucket into: capture moves, regular moves, walls near opponent,
    other walls.  Within each bucket the order doesn't matter much
    because alpha-beta will prune most of them anyway."""
    treasure_set = set()
    for t in game_state.treasures:
        treasure_set.add((t.row, t.col))
    opp = game_state.get_opponent()
    opr, opc = opp.row, opp.col

    captures = []
    moves = []
    walls_near = []
    walls_far = []

    for a in actions:
        if a.action_type == ACTION_MOVE:
            if a.target in treasure_set:
                captures.append(a)
            else:
                moves.append(a)
        else:
            wr, wc = a.target
            if abs(wr - opr) + abs(wc - opc) <= 2:
                walls_near.append(a)
            else:
                walls_far.append(a)

    return captures + moves + walls_near + walls_far


def _order_actions_walls_only(actions, game_state):
    """For deeper nodes, return only move actions + the single best
    wall candidate (wall closest to opponent).  This prevents the
    branching factor from exploding at depth >= 3."""
    treasure_set = set()
    for t in game_state.treasures:
        treasure_set.add((t.row, t.col))
    opp = game_state.get_opponent()
    opr, opc = opp.row, opp.col

    captures = []
    moves = []
    best_wall = None
    best_wall_dist = 999

    for a in actions:
        if a.action_type == ACTION_MOVE:
            if a.target in treasure_set:
                captures.append(a)
            else:
                moves.append(a)
        else:
            wr, wc = a.target
            d = abs(wr - opr) + abs(wc - opc)
            if d < best_wall_dist:
                best_wall_dist = d
                best_wall = a

    result = captures + moves
    if best_wall is not None:
        result.append(best_wall)
    return result


def alphabeta(game_state, depth: int, alpha: float, beta: float,
              maximizing: bool, maximizing_player_id: int) -> float:
    """
    Minimax with alpha-beta pruning, move ordering, TT, and
    wall-pruning at deeper levels.
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

    # At deeper levels, prune walls to only the best candidate
    if depth <= 2:
        actions = _order_actions_walls_only(actions, game_state)
    else:
        actions = _order_actions(actions, game_state)

    orig_alpha = alpha
    orig_beta = beta

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
                break
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
                break

    # Store in TT
    if len(_tt) < _TT_MAX_SIZE:
        if value <= orig_alpha:
            flag = _TT_UPPER
        elif value >= orig_beta:
            flag = _TT_LOWER
        else:
            flag = _TT_EXACT
        _tt[key] = (depth, flag, value)

    return value
