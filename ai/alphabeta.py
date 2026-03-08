"""
alphabeta.py — Optimized Alpha-Beta search for Maze Heist.

Goals of this version:
- safer transposition-table key (includes treasure positions and temp-wall timers)
- faster root/deep move ordering
- beam-style wall pruning at deeper nodes to keep branching under control
- slightly treasure-biased ordering so Minimax explores the whole maze
  instead of over-prioritising blocking in every position
"""

from game.actions import ACTION_MOVE
from game.board import CELL_EMPTY
from ai.heuristics import evaluate

_DIRS_AB = ((-1, 0), (1, 0), (0, -1), (0, 1))

_tt = {}
_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_TT_MAX_SIZE = 200000


def clear_transposition_table():
    _tt.clear()


def _temp_wall_signature(game_state):
    walls = getattr(game_state, "temp_walls", None)
    if not walls:
        return ()
    sig = []
    for w in walls:
        sig.append((w.row, w.col, getattr(w, "remaining_rounds", 0)))
    sig.sort()
    return tuple(sig)


def _treasure_signature(game_state):
    treasures = getattr(game_state, "treasures", None)
    if not treasures:
        return ()
    sig = []
    for t in treasures:
        sig.append((t.row, t.col, getattr(t, "value", 0)))
    sig.sort()
    return tuple(sig)


def _tt_key(game_state):
    """Safe TT key.

    The old key only used len(treasures) + board hash, which can alias
    different treasure layouts or temp-wall timers. This key keeps the
    table correct while staying compact for a 12x12 board.
    """
    cached = getattr(game_state, "_ab_tt_key", None)
    if cached is not None:
        return cached

    gs = game_state
    key = (
        gs.player1.row,
        gs.player1.col,
        gs.player1.score,
        getattr(gs.player1, "collected_count", 0),
        gs.player2.row,
        gs.player2.col,
        gs.player2.score,
        getattr(gs.player2, "collected_count", 0),
        gs.current_player_index,
        getattr(gs, "turn_count", 0),
        getattr(gs, "round_count", 0),
        _treasure_signature(gs),
        _temp_wall_signature(gs),
    )
    try:
        gs._ab_tt_key = key
    except Exception:
        pass
    return key


def _order_actions(actions, game_state):
    """Strategic ordering: captures → quiet moves → walls by quality.

    Wall quality considers chokepoint value (adjacent wall count) and
    proximity to contested treasures.  Walls stay after moves for good
    alpha-beta pruning, but the best wall is ordered first among walls.
    """
    treasure_values = {(t.row, t.col): t.value for t in game_state.treasures}
    opp = game_state.get_opponent()
    opr, opc = opp.row, opp.col
    grid = game_state.board.grid
    rows = game_state.board.rows
    cols = game_state.board.cols

    capture_moves = []
    quiet_moves = []
    walls = []

    for action in actions:
        if action.action_type == ACTION_MOVE:
            value = treasure_values.get(action.target, 0)
            if value:
                capture_moves.append((-value, action.target, action))
            else:
                quiet_moves.append(action)
        else:
            wr, wc = action.target
            # Chokepoint: more adjacent walls = narrower corridor = more impact
            adj_walls = 0
            for dr, dc in _DIRS_AB:
                nr, nc = wr + dr, wc + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != CELL_EMPTY:
                    adj_walls += 1
            dist_to_opp = abs(wr - opr) + abs(wc - opc)
            treasure_nearby = 0
            for (tr, tc), tv in treasure_values.items():
                if abs(wr - tr) + abs(wc - tc) <= 2:
                    treasure_nearby += tv
            quality = adj_walls * 5 + treasure_nearby - dist_to_opp
            walls.append((-quality, action.target, action))

    capture_moves.sort()
    walls.sort()

    result = [a for _, __, a in capture_moves]
    result.extend(quiet_moves)
    result.extend(a for _, __, a in walls)
    return result


def _beam_actions(actions, game_state, max_walls=2):
    """Keep all move actions and top-K walls, preserving strategic ordering.

    _order_actions places the best wall before quiet moves; this preserves
    that interleaving while capping total wall count.
    """
    ordered = _order_actions(actions, game_state)
    result = []
    wall_count = 0
    for action in ordered:
        if action.action_type == ACTION_MOVE:
            result.append(action)
        else:
            if wall_count < max_walls:
                result.append(action)
                wall_count += 1
    return result


def alphabeta(game_state, depth, alpha, beta, maximizing, maximizing_player_id):
    if depth == 0 or game_state.game_over:
        return evaluate(game_state, maximizing_player_id)

    key = _tt_key(game_state)
    tt_entry = _tt.get(key)
    if tt_entry is not None:
        tt_depth, tt_flag, tt_value = tt_entry
        if tt_depth >= depth:
            if tt_flag == _TT_EXACT:
                return tt_value
            if tt_flag == _TT_LOWER:
                alpha = max(alpha, tt_value)
            elif tt_flag == _TT_UPPER:
                beta = min(beta, tt_value)
            if alpha >= beta:
                return tt_value

    actions = game_state.get_all_actions()
    if not actions:
        return evaluate(game_state, maximizing_player_id)

    # Wider tree near leaf, narrower tree earlier when branching hurts most.
    if depth >= 3 and len(actions) > 6:
        actions = _beam_actions(actions, game_state, max_walls=2)
    else:
        actions = _order_actions(actions, game_state)

    orig_alpha = alpha
    orig_beta = beta

    if maximizing:
        value = float("-inf")
        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            score = alphabeta(child, depth - 1, alpha, beta, False, maximizing_player_id)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = float("inf")
        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            score = alphabeta(child, depth - 1, alpha, beta, True, maximizing_player_id)
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if len(_tt) < _TT_MAX_SIZE:
        if value <= orig_alpha:
            flag = _TT_UPPER
        elif value >= orig_beta:
            flag = _TT_LOWER
        else:
            flag = _TT_EXACT
        _tt[key] = (depth, flag, value)

    return value
