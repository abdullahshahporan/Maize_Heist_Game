"""
heuristics.py — Evaluation function used by Minimax (and reusable elsewhere).
Optimized: single BFS pass, inline mobility counting, fast terminal checks.

Design goals:
  - Strongly reward collecting treasures (score difference)
  - Reward moving toward high-value treasures (exploration)
  - Mildly reward blocking opponent from contested treasures
  - Penalise self-trapping (low mobility)
  - Balanced so Minimax explores the whole board, not camp in corners
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
      1. score_difference — primary driver
      2. treasure_potential — weighted sum of value/(dist+1) for all reachable treasures
      3. race_advantage — bonus when closer to high-value treasures than opponent
      4. mobility — penalise being boxed in, mild reward for open positions
      5. collection_progress — reward collecting more treasures
    """
    # Fast terminal check
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

    # 1. Score difference — most important
    score_diff = me.score - opp.score

    # 2 & 3. BFS from both players
    my_dists = _fast_bfs(grid, rows, cols, me.row, me.col)
    opp_dists = _fast_bfs(grid, rows, cols, opp.row, opp.col)

    # Treasure potential: sum value/(dist+1) for all reachable treasures
    # Race advantage: bonus when I'm closer to a treasure than opponent
    my_treasure_potential = 0.0
    opp_treasure_potential = 0.0
    race_advantage = 0.0

    for t in game_state.treasures:
        tp = (t.row, t.col)
        d_me = my_dists.get(tp, 999)
        d_opp = opp_dists.get(tp, 999)

        if d_me < 999:
            my_treasure_potential += t.value / (d_me + 1)
        if d_opp < 999:
            opp_treasure_potential += t.value / (d_opp + 1)

        # Race bonus: who gets there first?
        if d_me < 999 and d_opp < 999:
            if d_me < d_opp:
                race_advantage += t.value * 0.3  # I'm closer
            elif d_opp < d_me:
                race_advantage -= t.value * 0.15  # opponent closer (mild penalty)

    treasure_diff = my_treasure_potential - opp_treasure_potential

    # 4. Mobility
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

    # Self-trap penalty (strong) — don't get boxed in
    if my_moves == 0:
        trap_penalty = 25.0
    elif my_moves == 1:
        trap_penalty = 10.0
    elif my_moves == 2:
        trap_penalty = 3.0
    else:
        trap_penalty = 0.0

    # 5. Blocking reward — scale with how boxed the opponent is
    #    0 moves → huge reward, 1 move → good, 2 → mild
    if opp_moves == 0:
        blocking_bonus = 15.0
    elif opp_moves == 1:
        blocking_bonus = 8.0
    elif opp_moves == 2:
        blocking_bonus = 3.0
    else:
        blocking_bonus = 0.0

    # 6. Opponent-path disruption — reward if opponent is far from
    #    the nearest treasure (i.e. blocking is working)
    nearest_opp_treasure_dist = 999
    for t in game_state.treasures:
        tp = (t.row, t.col)
        d = opp_dists.get(tp, 999)
        if d < nearest_opp_treasure_dist:
            nearest_opp_treasure_dist = d
    if nearest_opp_treasure_dist < 999:
        path_disruption = nearest_opp_treasure_dist * 0.5
    else:
        path_disruption = 10.0  # opponent completely cut off

    # 7. Collection progress bonus
    collection_diff = me.collected_count - opp.collected_count

    return (
        10.0 * score_diff           # Collected score is king
        + 2.5 * treasure_diff       # Prefer positions closer to treasures
        + 2.0 * race_advantage      # Prefer being closer than opponent
        + blocking_bonus            # Reward boxing opponent in
        + path_disruption           # Reward increasing opponent's path length
        - trap_penalty              # Don't self-trap
        + 3.0 * collection_diff     # Reward collecting more items
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
