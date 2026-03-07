"""
heuristics.py — Evaluation function used by Minimax (and reusable elsewhere).
Optimized: single BFS pass, inline mobility counting, fast terminal checks.
"""

from collections import deque
from game.board import CELL_EMPTY

# Pre-computed direction offsets
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def evaluate(game_state, maximizing_player_id: int) -> float:
    """
    Evaluate the game state from the perspective of *maximizing_player_id*.
    Higher is better for that player.

    Components:
      - score_difference
      - distance to best treasure (value/distance weighted)
      - opponent distance to competing treasures
      - mobility difference
      - blocking advantage
      - self-trap risk penalty
    """
    # Fast terminal check first
    if game_state.game_over:
        w = game_state.winner
        if w is not None:
            return 10000.0 if w.id == maximizing_player_id else -10000.0
        return 0.0  # draw

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

    # 1. Score difference
    score_diff = me.score - opp.score

    # 2 & 3. BFS from both players — single pass each, inlined for speed
    my_dists = _fast_bfs(grid, rows, cols, me.row, me.col)
    opp_dists = _fast_bfs(grid, rows, cols, opp.row, opp.col)

    # Find best treasure by value/distance ratio
    best_treasure_val = 0.0
    my_dist_best = 0.0
    opp_dist_best = 0.0

    for t in game_state.treasures:
        tp = (t.row, t.col)
        d_me = my_dists.get(tp, 999)
        d_opp = opp_dists.get(tp, 999)
        val = t.value / (d_me + 1)
        if val > best_treasure_val:
            best_treasure_val = val
            my_dist_best = d_me
            opp_dist_best = d_opp

    # 4. Mobility — inline count of walkable non-opponent neighbors
    mr, mc = me.row, me.col
    opr, opc = opp.row, opp.col
    my_moves = 0
    for dr, dc in _DIRS:
        nr, nc = mr + dr, mc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)):
            my_moves += 1

    opp_moves = 0
    for dr, dc in _DIRS:
        nr, nc = opr + dr, opc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == mr and nc == mc)):
            opp_moves += 1

    mobility_diff = my_moves - opp_moves

    # 5. Blocking advantage
    blocking_advantage = max(0, 4 - opp_moves)

    # 6. Self-trap risk
    if my_moves <= 1:
        trap_risk = 1.0
    elif my_moves == 2:
        trap_risk = 0.3
    else:
        trap_risk = 0.0

    return (
        10.0 * score_diff
        - 2.0 * my_dist_best
        + 2.0 * opp_dist_best
        + 3.0 * mobility_diff
        + 5.0 * blocking_advantage
        - 8.0 * trap_risk
    )


def _fast_bfs(grid, rows: int, cols: int, sr: int, sc: int) -> dict:
    """Inlined BFS flood-fill returning {(r,c): dist} dict.
    Avoids Board method calls for maximum speed inside evaluation."""
    start = (sr, sc)
    visited = {start: 0}
    queue = deque()
    queue.append((sr, sc, 0))

    while queue:
        r, c, dist = queue.popleft()
        nd = dist + 1
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = (nr, nc)
                if nb not in visited and grid[nr][nc] == CELL_EMPTY:
                    visited[nb] = nd
                    queue.append((nr, nc, nd))
    return visited
