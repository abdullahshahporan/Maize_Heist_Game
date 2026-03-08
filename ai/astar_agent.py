"""
astar_agent.py — Stronger and faster A* + tactical controller.

Main improvements:
- uses exact BFS distances for full-maze treasure evaluation
- considers the whole reachable maze through treasure-potential scoring
- keeps wall usage available, but prefers efficient treasure racing
- biases toward A* winning more often by prioritising capture tempo
"""

from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from game.board import CELL_EMPTY
from game.rules import get_valid_moves
from utils.pathfinding import astar, bfs_all_distances
from ai.tactical_blocker import evaluate_wall_placements

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_WALL_BASE_THRESHOLD = 2.5
_CAPTURE_WIN_SCORE = 1000.0


def _mobility(pos, opp_pos, grid, rows, cols):
    r, c = pos
    orow, ocol = opp_pos
    total = 0
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if (
            0 <= nr < rows
            and 0 <= nc < cols
            and grid[nr][nc] == CELL_EMPTY
            and not (nr == orow and nc == ocol)
        ):
            total += 1
    return total


def _score_target(treasure, my_dists, opp_dists):
    tp = (treasure.row, treasure.col)
    d_me = my_dists.get(tp, 10**9)
    d_opp = opp_dists.get(tp, 10**9)
    if d_me == 10**9:
        return float("-inf")

    score = (treasure.value * 2.0) / (d_me + 1)
    if d_opp != 10**9:
        lead = d_opp - d_me
        score += lead * treasure.value * 0.40
        if d_me < d_opp:
            score += treasure.value * 0.30
        elif d_opp < d_me:
            score -= treasure.value * 0.15
    return score


def _treasure_potential_from_dists(move_dists, opp_dists, treasures):
    total = 0.0
    reachable = 0
    for t in treasures:
        tp = (t.row, t.col)
        d_me = move_dists.get(tp, 10**9)
        if d_me == 10**9:
            continue
        reachable += 1
        value_term = (t.value * 1.7) / (d_me + 1)
        d_opp = opp_dists.get(tp, 10**9)
        race_term = 0.0
        if d_opp != 10**9:
            if d_me < d_opp:
                race_term += t.value * 0.30
            elif d_opp < d_me:
                race_term -= t.value * 0.15
        total += value_term + race_term
    return total, reachable


def _evaluate_move(game_state, move_pos, move_dists, opp_dists, treasures, grid, rows, cols, target_step):
    score = 0.0
    capture_value = 0
    for t in treasures:
        if (t.row, t.col) == move_pos:
            capture_value = max(capture_value, t.value)
    if capture_value:
        score += _CAPTURE_WIN_SCORE + capture_value * 20.0

    potential, reachable = _treasure_potential_from_dists(move_dists, opp_dists, treasures)
    score += potential
    score += reachable * 0.35

    if target_step is not None and move_pos == target_step:
        score += 5.5

    opp_pos = (game_state.get_opponent().row, game_state.get_opponent().col)
    mob = _mobility(move_pos, opp_pos, grid, rows, cols)
    if mob == 0:
        score -= 35.0
    elif mob == 1:
        score -= 9.0
    elif mob == 2:
        score -= 2.0
    else:
        score += min(mob, 4) * 0.4

    # Small centre/exploration bonus so the agent does not hug corners.
    center_r = rows // 2
    center_c = cols // 2
    score -= 0.08 * (abs(move_pos[0] - center_r) + abs(move_pos[1] - center_c))
    return score


def choose_action_astar(game_state):
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board
    treasures = game_state.treasures
    grid = board.grid
    rows, cols = board.rows, board.cols

    valid_moves = get_valid_moves(board, player, opponent)
    if not valid_moves:
        actions = game_state.get_all_actions()
        return actions[0] if actions else None

    my_dists = bfs_all_distances(board, player.pos)
    opp_dists = bfs_all_distances(board, opponent.pos)

    best_target = None
    best_target_score = float("-inf")
    for t in treasures:
        target_score = _score_target(t, my_dists, opp_dists)
        if target_score > best_target_score:
            best_target_score = target_score
            best_target = t

    target_step = None
    if best_target is not None:
        path = astar(board, player.pos, best_target.pos, blocked_extra={opponent.pos})
        if path and len(path) > 1:
            target_step = path[1]

    best_move_action = None
    best_move_score = float("-inf")
    immediate_capture = False

    for mv in valid_moves:
        move_dists = bfs_all_distances(board, mv)
        move_score = _evaluate_move(
            game_state,
            mv,
            move_dists,
            opp_dists,
            treasures,
            grid,
            rows,
            cols,
            target_step,
        )
        if move_score >= _CAPTURE_WIN_SCORE:
            immediate_capture = True
        if move_score > best_move_score:
            best_move_score = move_score
            best_move_action = Action(ACTION_MOVE, mv)

    if immediate_capture:
        return best_move_action

    wall_options = evaluate_wall_placements(
        game_state,
        self_dists_before=my_dists,
        opp_dists_before=opp_dists,
        max_candidates=6,
    )
    best_wall_action = None
    best_wall_utility = float("-inf")
    if wall_options:
        best_wall_pos, best_wall_utility = wall_options[0]
        best_wall_action = Action(ACTION_PLACE_WALL, best_wall_pos)

    score_diff = player.score - opponent.score
    wall_threshold = _WALL_BASE_THRESHOLD
    if score_diff < -15:
        wall_threshold = 1.2
    elif score_diff < -5:
        wall_threshold = 1.8
    elif score_diff > 10:
        wall_threshold = 3.5

    # Place wall only when utility clearly exceeds threshold and
    # the tactical gain justifies skipping a move.
    if (best_wall_action
            and best_wall_utility > wall_threshold
            and best_wall_utility > 0.06 * best_move_score):
        return best_wall_action

    if best_move_action is not None:
        return best_move_action
    if best_wall_action is not None:
        return best_wall_action

    actions = game_state.get_all_actions()
    return actions[0] if actions else None
