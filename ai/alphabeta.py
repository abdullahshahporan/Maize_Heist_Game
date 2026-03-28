"""
alphabeta.py — Optimized Alpha-Beta search for Maze Heist.

Goals of this version:
- safer transposition-table key (includes treasure positions and temp-wall timers)
- aggressive move ordering favoring captures, blocking walls, then mobility
- wider wall beam at deeper nodes to allow more blocking options
- late-move reduction for deeper/wider search
- treasure-biased ordering with opponent path awareness
"""

from game.actions import ACTION_MOVE, ACTION_PLACE_WALL
from game.board import CELL_EMPTY
from ai.heuristics import evaluate

_DIRS_AB = ((-1, 0), (1, 0), (0, -1), (0, 1))

_tt = {}
_history = {}
_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_TT_MAX_SIZE = 300000


def clear_transposition_table():
    _tt.clear()
    _history.clear()


def _action_key(action):
    return (action.action_type, action.target)


def _temp_wall_signature(game_state):
    walls = getattr(game_state, "temp_walls", None)
    if not walls:
        return ()
    sig = []
    for wall in walls:
        sig.append((wall.row, wall.col, getattr(wall, "remaining_rounds", 0)))
    sig.sort()
    return tuple(sig)


def _treasure_signature(game_state):
    treasures = getattr(game_state, "treasures", None)
    if not treasures:
        return ()
    sig = []
    for treasure in treasures:
        sig.append((treasure.row, treasure.col, getattr(treasure, "value", 0)))
    sig.sort()
    return tuple(sig)


def _tt_key(game_state):
    """Safe TT key for cached search results."""
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
    """Strategic ordering: captures → blocking walls → quiet moves → other walls."""
    treasure_values = game_state.get_treasure_value_map()
    player = game_state.get_current_player()
    opp = game_state.get_opponent()
    pr, pc = player.row, player.col
    opr, opc = opp.row, opp.col
    grid = game_state.board.grid
    rows = game_state.board.rows
    cols = game_state.board.cols

    capture_moves = []
    quiet_moves = []
    walls = []

    for action in actions:
        history = _history.get(_action_key(action), 0)
        if action.action_type == ACTION_MOVE:
            value = treasure_values.get(action.target, 0)
            if value:
                capture_moves.append((-(value * 100 + history), action.target, action))
                continue

            mr, mc = action.target
            treasure_pull = 0.0
            for (tr, tc), tv in treasure_values.items():
                dist = abs(mr - tr) + abs(mc - tc)
                if dist <= 6:
                    treasure_pull += tv / (dist + 1)

            mobility = 0
            for dr, dc in _DIRS_AB:
                nr, nc = mr + dr, mc + dc
                if (
                    0 <= nr < rows
                    and 0 <= nc < cols
                    and grid[nr][nc] == CELL_EMPTY
                    and not (nr == opr and nc == opc)
                ):
                    mobility += 1

            # Bonus for moving toward opponent (enables future blocking)
            opp_dist_before = abs(pr - opr) + abs(pc - opc)
            opp_dist_after = abs(mr - opr) + abs(mc - opc)
            approach_bonus = max(0, opp_dist_before - opp_dist_after) * 3.0

            center_bias = abs(mr - rows // 2) + abs(mc - cols // 2)
            step_gain = abs(pr - mr) + abs(pc - mc)
            score = treasure_pull * 12.0 + mobility * 4.0 + step_gain + approach_bonus - center_bias
            quiet_moves.append((-(score + history * 0.02), action.target, action))
            continue

        wr, wc = action.target
        # Wall scoring: prioritize walls that block opponent
        adj_walls = 0
        for dr, dc in _DIRS_AB:
            nr, nc = wr + dr, wc + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != CELL_EMPTY:
                adj_walls += 1

        dist_to_opp = abs(wr - opr) + abs(wc - opc)

        # Strong bonus for walls adjacent to opponent
        opp_adjacent = (dist_to_opp == 1)
        opp_near_bonus = 15.0 if opp_adjacent else (5.0 if dist_to_opp <= 2 else 0.0)

        # Bonus for walls near treasures opponent is close to
        treasure_block = 0
        for (tr, tc), tv in treasure_values.items():
            wall_to_t = abs(wr - tr) + abs(wc - tc)
            opp_to_t = abs(opr - tr) + abs(opc - tc)
            if wall_to_t <= 2 and opp_to_t <= 4:
                treasure_block += tv * 1.5

        # Check if wall reduces opponent mobility
        opp_mobility_impact = 0
        for dr, dc in _DIRS_AB:
            nr, nc = opr + dr, opc + dc
            if (nr, nc) == (wr, wc):
                opp_mobility_impact += 8  # blocks one of opponent's moves

        quality = (adj_walls * 3 + treasure_block + opp_near_bonus
                   + opp_mobility_impact - dist_to_opp * 0.3 + history * 0.03)
        walls.append((-quality, action.target, action))

    capture_moves.sort()
    quiet_moves.sort()
    walls.sort()

    # Walls that actively block the opponent (quality ≥ 18, e.g. adjacent to
    # opponent or sitting on their treasure path) are placed BEFORE quiet moves
    # so alpha-beta cannot prune them before they are explored.  Weak walls
    # stay at the end so they do not waste search budget.
    _HIGH_WALL_Q = 18.0
    high_walls = [(s, t, a) for s, t, a in walls if -s >= _HIGH_WALL_Q]
    low_walls  = [(s, t, a) for s, t, a in walls if -s <  _HIGH_WALL_Q]

    result = [action for _, __, action in capture_moves]
    result.extend(action for _, __, action in high_walls)
    result.extend(action for _, __, action in quiet_moves)
    result.extend(action for _, __, action in low_walls)
    return result


def _beam_actions(actions, game_state, max_walls=5):
    """Keep all move actions and top-K walls, preserving strategic ordering."""
    ordered = _order_actions(actions, game_state)
    result = []
    wall_count = 0
    for action in ordered:
        if action.action_type != ACTION_PLACE_WALL:
            result.append(action)
        elif wall_count < max_walls:
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

    if depth >= 3 and len(actions) > 6:
        actions = _beam_actions(actions, game_state, max_walls=3)
    else:
        actions = _order_actions(actions, game_state)

    orig_alpha = alpha
    orig_beta = beta

    if maximizing:
        value = float("-inf")
        for i, action in enumerate(actions):
            child = game_state.clone()
            child.apply_action(action)
            # Late-move reduction: search later moves at reduced depth
            if i >= 4 and depth >= 3 and action.action_type != ACTION_MOVE:
                score = alphabeta(child, depth - 2, alpha, beta, False, maximizing_player_id)
                if score > alpha:
                    # Re-search at full depth if it looks promising
                    score = alphabeta(child, depth - 1, alpha, beta, False, maximizing_player_id)
            else:
                score = alphabeta(child, depth - 1, alpha, beta, False, maximizing_player_id)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                _history[_action_key(action)] = _history.get(_action_key(action), 0) + depth * depth
                break
    else:
        value = float("inf")
        for i, action in enumerate(actions):
            child = game_state.clone()
            child.apply_action(action)
            # Late-move reduction for minimizing player too
            if i >= 4 and depth >= 3 and action.action_type != ACTION_MOVE:
                score = alphabeta(child, depth - 2, alpha, beta, True, maximizing_player_id)
                if score < beta:
                    score = alphabeta(child, depth - 1, alpha, beta, True, maximizing_player_id)
            else:
                score = alphabeta(child, depth - 1, alpha, beta, True, maximizing_player_id)
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                _history[_action_key(action)] = _history.get(_action_key(action), 0) + depth * depth
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
