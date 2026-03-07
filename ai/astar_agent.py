"""
astar_agent.py — AI Agent 2: A* pathfinding + Tactical Wall Placement.

Strategy:
1. BFS flood-fill from both players for distance maps.
2. Pick best treasure target by value/distance + race awareness.
3. For each valid move, do a 1-ply simulation: apply move, then
   re-evaluate treasure potential from the new position.
4. Evaluate wall placements via tactical blocker layer.
5. If behind on score, lower wall threshold to block more aggressively.
6. Compare best move vs best wall and choose action.

Improved: 1-ply lookahead per move, multi-target evaluation, adaptive
blocking, avoidance of dead-end positions.
"""

from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from game.board import CELL_EMPTY
from game.rules import get_valid_moves
from utils.pathfinding import astar, bfs_all_distances
from ai.tactical_blocker import evaluate_wall_placements

# Base utility threshold for wall placement
_WALL_BASE_THRESHOLD = 0.8
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _treasure_potential(pos, treasures, opp_dists):
    """Sum of value/(manhattan_dist+1) for all treasures from given pos,
    with race bonus when closer than opponent."""
    r, c = pos
    total = 0.0
    for t in treasures:
        d = abs(r - t.row) + abs(c - t.col)
        total += t.value / (d + 1)
        d_opp = opp_dists.get((t.row, t.col), 999)
        if d < d_opp:
            total += t.value * 0.2  # race advantage
    return total


def _mobility(pos, opp_pos, grid, rows, cols):
    """Count walkable neighbors from pos."""
    mr, mc = pos
    opr, opc = opp_pos
    count = 0
    for dr, dc in _DIRS:
        nr, nc = mr + dr, mc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)):
            count += 1
    return count


def _evaluate_move_1ply(game_state, move_pos, treasures, opp_dists, grid,
                        rows, cols, path_next):
    """Evaluate a move with 1-ply simulation."""
    mr, mc = move_pos

    score = 0.0

    # Immediate treasure capture — highest priority
    for t in treasures:
        if (t.row, t.col) == move_pos:
            score += t.value * 5.0

    # Treasure potential from new position
    score += _treasure_potential(move_pos, treasures, opp_dists)

    # Bonus for being on optimal A* path
    if move_pos == path_next:
        score += 4.0

    # Mobility check — avoid dead ends
    opp_pos = (game_state.get_opponent().row, game_state.get_opponent().col)
    mob = _mobility(move_pos, opp_pos, grid, rows, cols)
    if mob == 0:
        score -= 30.0  # completely stuck
    elif mob == 1:
        score -= 8.0   # dead end
    elif mob == 2:
        score -= 1.5   # corridor

    # 1-ply simulation: from this new position, what's the best BFS
    # distance to the nearest high-value treasure?
    best_reachable = 0.0
    for t in treasures:
        if (t.row, t.col) == move_pos:
            continue  # already counted as capture
        d = abs(mr - t.row) + abs(mc - t.col)
        val = t.value / (d + 1)
        if val > best_reachable:
            best_reachable = val
    score += best_reachable * 1.5

    return score


def choose_action_astar(game_state) -> Action:
    """Main decision function for the A* + tactical agent."""
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board

    # BFS from both players
    my_dists = bfs_all_distances(board, player.pos)
    opp_dists = bfs_all_distances(board, opponent.pos)

    treasures = game_state.treasures
    grid = board.grid
    rows, cols = board.rows, board.cols
    valid_moves = get_valid_moves(board, player, opponent)

    # ── Pick best treasure target ───────────────────────
    best_target = None
    best_target_score = float('-inf')
    for t in treasures:
        tp = (t.row, t.col)
        d_me = my_dists.get(tp, -1)
        d_opp = opp_dists.get(tp, -1)
        if d_me < 0:
            continue
        s = t.value / (d_me + 1)
        if d_opp >= 0:
            lead = d_opp - d_me
            s += lead * t.value * 0.3
        if s > best_target_score:
            best_target_score = s
            best_target = t

    # ── A* path to target ──────────────────────────────
    path_next = None
    if best_target:
        blocked = {opponent.pos}
        path = astar(board, player.pos, best_target.pos, blocked)
        if path and len(path) > 1:
            path_next = path[1]

    # ── Evaluate each valid move ────────────────────────
    best_move_action = None
    best_move_score = float('-inf')

    for mv in valid_moves:
        score = _evaluate_move_1ply(game_state, mv, treasures, opp_dists,
                                    grid, rows, cols, path_next)
        if score > best_move_score:
            best_move_score = score
            best_move_action = Action(ACTION_MOVE, mv)

    # ── Evaluate wall placements ────────────────────────
    wall_options = evaluate_wall_placements(game_state)
    best_wall_action = None
    best_wall_utility = float('-inf')
    if wall_options:
        best_wall_pos, best_wall_utility = wall_options[0]
        best_wall_action = Action(ACTION_PLACE_WALL, best_wall_pos)

    # ── Adaptive wall threshold ─────────────────────────
    score_diff = player.score - opponent.score
    threshold = _WALL_BASE_THRESHOLD
    if score_diff < -15:
        threshold = 0.2   # desperate
    elif score_diff < -5:
        threshold = 0.4
    elif score_diff < 0:
        threshold = 0.6

    # ── Compare move vs wall ────────────────────────────
    # Only place wall if the utility clearly outweighs moving
    if (best_wall_action
            and best_wall_utility > threshold
            and best_move_action):
        return best_wall_action

    if best_move_action:
        return best_move_action

    if best_wall_action:
        return best_wall_action

    actions = game_state.get_all_actions()
    return actions[0] if actions else None
