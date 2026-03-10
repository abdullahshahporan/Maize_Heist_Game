"""
heuristics.py — Aggressive board evaluation for Minimax.

Key design:
- Heavy score_diff weight so Minimax always prioritizes point collection
- Strong race_score with wall-aware BFS to justify blocking walls
- Boosted blocking bonuses to reward trapping the opponent
- Endgame urgency: when few treasures remain, aggression increases
"""

from collections import deque
from game.board import CELL_EMPTY

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INF = 10 ** 9


def evaluate(game_state, maximizing_player_id):
    if game_state.game_over:
        winner = game_state.winner
        if winner is None:
            return 0.0
        return 10000.0 if winner.id == maximizing_player_id else -10000.0

    if maximizing_player_id == 1:
        me = game_state.player1
        opp = game_state.player2
    else:
        me = game_state.player2
        opp = game_state.player1

    board = game_state.board
    grid = board.grid
    rows = board.rows
    cols = board.cols

    my_dists = _fast_bfs(grid, rows, cols, me.row, me.col)
    opp_dists = _fast_bfs(grid, rows, cols, opp.row, opp.col)

    score_diff = me.score - opp.score
    collection_diff = getattr(me, "collected_count", 0) - getattr(opp, "collected_count", 0)

    # ── Treasure race analysis ──────────────────────────
    # Continuous lead formula: walls that increase d_opp directly boost
    # race_score, proportional to treasure value and proximity.
    race_score = 0.0
    my_reachable = 0
    opp_reachable = 0
    total_my_dist = 0
    total_opp_dist = 0

    for t in game_state.treasures:
        tp = (t.row, t.col)
        d_me = my_dists.get(tp, _INF)
        d_opp = opp_dists.get(tp, _INF)

        me_can = d_me < _INF
        opp_can = d_opp < _INF

        if me_can:
            my_reachable += 1
            total_my_dist += d_me
        if opp_can:
            opp_reachable += 1
            total_opp_dist += d_opp

        if me_can and opp_can:
            lead = d_opp - d_me  # positive = I'm closer
            weight = t.value / (min(d_me, d_opp) + 1)
            race_score += lead * weight * 1.3
            # Extra tempo bonus: if I'm strictly closer, I capture first
            if d_me < d_opp:
                race_score += t.value * 0.5
        elif me_can:
            # Opponent cut off from this treasure — big advantage
            race_score += t.value * 4.0
        elif opp_can:
            # I'm cut off — big disadvantage
            race_score -= t.value * 4.0

    # Average distance comparison: walls increase opponent's avg distance
    avg_my = total_my_dist / max(my_reachable, 1)
    avg_opp = total_opp_dist / max(opp_reachable, 1)
    dist_advantage = avg_opp - avg_my

    # ── Mobility analysis ───────────────────────────────
    my_moves = _count_open_neighbors(grid, rows, cols, me.row, me.col, opp.row, opp.col)
    opp_moves = _count_open_neighbors(grid, rows, cols, opp.row, opp.col, me.row, me.col)

    # Trap avoidance
    if my_moves == 0:
        trap_penalty = 35.0
    elif my_moves == 1:
        trap_penalty = 14.0
    elif my_moves == 2:
        trap_penalty = 3.5
    else:
        trap_penalty = 0.0

    # Blocking reward — walls directly reduce opponent mobility
    if opp_moves == 0:
        blocking_bonus = 18.0
    elif opp_moves == 1:
        blocking_bonus = 9.0
    elif opp_moves == 2:
        blocking_bonus = 3.5
    else:
        blocking_bonus = 0.0

    # ── Map control ─────────────────────────────────────
    reachable_diff = my_reachable - opp_reachable
    control = len(my_dists) - len(opp_dists)

    # ── Endgame urgency ─────────────────────────────
    n_treasures = len(game_state.treasures)
    urgency = 1.0
    if n_treasures <= 3:
        urgency = 1.6
    elif n_treasures <= 6:
        urgency = 1.25

    return (
        10.0 * score_diff
        + 2.8 * race_score * urgency
        + 0.8 * dist_advantage
        + 3.5 * reachable_diff
        + 0.10 * control
        + blocking_bonus * 1.2
        + 1.4 * (my_moves - opp_moves)
        - trap_penalty
        + 2.5 * collection_diff
    )


def _count_open_neighbors(grid, rows, cols, r, c, block_r, block_c):
    total = 0
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if (
            0 <= nr < rows
            and 0 <= nc < cols
            and grid[nr][nc] == CELL_EMPTY
            and not (nr == block_r and nc == block_c)
        ):
            total += 1
    return total


def _fast_bfs(grid, rows, cols, sr, sc):
    start = (sr, sc)
    visited = {start: 0}
    queue = deque([(sr, sc)])

    while queue:
        r, c = queue.popleft()
        nd = visited[(r, c)] + 1
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = (nr, nc)
                if nb not in visited and grid[nr][nc] == CELL_EMPTY:
                    visited[nb] = nd
                    queue.append((nr, nc))
    return visited
