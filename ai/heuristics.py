"""
heuristics.py — Hyper-aggressive board evaluation for Minimax.

Key design:
- Very heavy score_diff so Minimax grabs every point possible
- Dominant race_score: being closer to treasures is hugely valuable
- Massive blocking bonuses: trapping opponent is nearly as good as scoring
- Denial scoring: cutting opponent off from treasures is rewarded heavily
- Proximity aggression: moving toward opponent to restrict them
- Endgame escalation: when few treasures remain, go all-in
"""

from collections import deque
from game.board import CELL_EMPTY

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INF = 10 ** 9


def _cached_bfs(game_state, row, col):
    cache = getattr(game_state, "_distance_cache", None)
    key = (row, col)
    if cache is not None and key in cache:
        return cache[key]

    board = game_state.board
    dists = _fast_bfs(board.grid, board.rows, board.cols, row, col)
    if cache is not None:
        cache[key] = dists
    return dists


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

    my_dists = _cached_bfs(game_state, me.row, me.col)
    opp_dists = _cached_bfs(game_state, opp.row, opp.col)

    score_diff = me.score - opp.score
    collection_diff = getattr(me, "collected_count", 0) - getattr(opp, "collected_count", 0)

    # ── Treasure race analysis (aggressive) ─────────────
    race_score = 0.0
    my_reachable = 0
    opp_reachable = 0
    total_my_dist = 0
    total_opp_dist = 0
    denial_bonus = 0.0          # reward for cutting opponent off treasures
    imminent_capture = 0.0      # I can capture next turn

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
            race_score += lead * weight * 1.8
            # Tempo bonus: if I'm strictly closer, I capture first
            if d_me < d_opp:
                race_score += t.value * 0.7
                # Imminent capture bonus: I get it next turn
                if d_me == 1:
                    imminent_capture += t.value * 3.0
                elif d_me == 2:
                    imminent_capture += t.value * 1.0
                elif d_me == 3:
                    imminent_capture += t.value * 0.3
            elif d_opp < d_me:
                # Opponent is closer — penalize but also incentivize blocking
                race_score -= t.value * 0.3
                # Blocking incentive: if opponent is 1-2 away, walls are critical
                if d_opp <= 2:
                    race_score -= t.value * 0.5  # extra urgency
        elif me_can:
            # Opponent completely cut off — massive advantage
            denial_bonus += t.value * 5.0
            if d_me <= 2:
                denial_bonus += t.value * 2.0  # easy pickup too
        elif opp_can:
            # I'm cut off — significant disadvantage
            race_score -= t.value * 5.0

    # ── Opponent imminent threat penalty ────────────────
    # Explicit penalty whenever A* is about to collect a high-value treasure.
    # This creates a strong blocking signal regardless of where Minimax is,
    # making walls near those treasures look very valuable in the search tree.
    opp_imminent_threat = 0.0
    for t in game_state.treasures:
        tp = (t.row, t.col)
        d_opp = opp_dists.get(tp, _INF)
        if d_opp == 1:
            opp_imminent_threat += t.value * 5.0   # opponent captures next turn
        elif d_opp == 2:
            opp_imminent_threat += t.value * 2.5
        elif d_opp == 3:
            opp_imminent_threat += t.value * 1.0

    # Average distance comparison
    avg_my = total_my_dist / max(my_reachable, 1)
    avg_opp = total_opp_dist / max(opp_reachable, 1)
    dist_advantage = avg_opp - avg_my

    # ── Difficulty-scaled blocking aggression ───────────
    # Easy: Minimax blocks when clearly beneficial to deny A*
    # Hard: very aggressive blocker
    _diff = getattr(game_state, 'difficulty', 'medium')
    _block_scale = {'easy': 0.70, 'medium': 0.95, 'hard': 1.40}.get(_diff, 0.95)

    # ── Mobility analysis ────────────────────────────────
    my_moves = _count_open_neighbors(grid, rows, cols, me.row, me.col, opp.row, opp.col)
    opp_moves = _count_open_neighbors(grid, rows, cols, opp.row, opp.col, me.row, me.col)

    # Trap avoidance — always penalized regardless of difficulty
    if my_moves == 0:
        trap_penalty = 50.0
    elif my_moves == 1:
        trap_penalty = 18.0
    elif my_moves == 2:
        trap_penalty = 4.0
    else:
        trap_penalty = 0.0

    # Blocking reward — scaled by difficulty
    if opp_moves == 0:
        blocking_bonus = 40.0   # opponent is completely trapped
    elif opp_moves == 1:
        blocking_bonus = 20.0   # opponent nearly trapped
    elif opp_moves == 2:
        blocking_bonus = 7.0    # opponent restricted
    else:
        blocking_bonus = 0.0

    # ── Corridor trapping detection (difficulty-scaled) ──
    opp_freedom = len(opp_dists)
    my_freedom = len(my_dists)
    corridor_bonus = 0.0
    if opp_freedom <= 6:
        corridor_bonus = 22.0
    elif opp_freedom <= 12:
        corridor_bonus = 9.0
    elif opp_freedom <= 20:
        corridor_bonus = 2.5

    # ── Proximity aggression (difficulty-scaled) ─────────
    opp_dist_from_me = abs(me.row - opp.row) + abs(me.col - opp.col)
    proximity_bonus = 0.0
    if opp_dist_from_me <= 3 and opp_moves <= 2:
        proximity_bonus = 5.0
    elif opp_dist_from_me <= 2:
        proximity_bonus = 1.5

    # ── Blocking-position bonus (path interception guide) ──
    # Reward Minimax for being adjacent to A*'s path corridor to nearby
    # treasures.  Walls can ONLY be placed on adjacent cells, so being next
    # to A*'s route means Minimax can intercept on the very next turn.
    # This term drives the search tree to move Minimax into intercept positions
    # even when no wall can be placed in the current state.
    blocking_pos_bonus = 0.0
    for dr, dc in _DIRS:
        nr, nc = me.row + dr, me.col + dc
        if not (0 <= nr < rows and 0 <= nc < cols):
            continue
        if grid[nr][nc] != CELL_EMPTY:
            continue
        if nr == opp.row and nc == opp.col:
            continue
        cell = (nr, nc)
        d_opp_to_cell = opp_dists.get(cell, _INF)
        if d_opp_to_cell >= _INF:
            continue
        for t in game_state.treasures:
            d_opp_to_t = opp_dists.get((t.row, t.col), _INF)
            if d_opp_to_t >= _INF:
                continue
            # Cell lies on A*'s BFS path when opp→cell + cell→t ≈ opp→t
            d_cell_to_t = abs(nr - t.row) + abs(nc - t.col)
            if d_opp_to_cell + d_cell_to_t <= d_opp_to_t + 1:
                blocking_pos_bonus += t.value * 1.5

    # ── Map control ─────────────────────────────────────
    reachable_diff = my_reachable - opp_reachable
    control = my_freedom - opp_freedom

    # ── Endgame urgency ──────────────────────────────────
    n_treasures = len(game_state.treasures)
    urgency = 1.0
    if n_treasures <= 2:
        urgency = 2.0
    elif n_treasures <= 4:
        urgency = 1.6
    elif n_treasures <= 7:
        urgency = 1.3

    # ── Wall-overuse penalty ──────────────────────────────
    # Penalize Minimax in the search tree when it has placed significantly
    # more walls than the opponent.  This teaches the tree that spending
    # turns on walls instead of collecting treasures hurts the score.
    my_walls = getattr(me, 'walls_placed', 0)
    opp_walls = getattr(opp, 'walls_placed', 0)
    wall_overuse_penalty = max(0.0, (my_walls - opp_walls - 2)) * 5.5 * _block_scale

    return (
        14.0 * score_diff
        + 5.0 * race_score * urgency
        + imminent_capture * urgency
        + 2.0 * dist_advantage
        + 5.5 * reachable_diff
        + 0.15 * control
        + blocking_bonus * 1.5 * _block_scale
        + corridor_bonus * _block_scale
        + proximity_bonus * _block_scale
        + blocking_pos_bonus * _block_scale
        + 1.8 * (my_moves - opp_moves)
        - trap_penalty
        + denial_bonus * urgency * _block_scale
        + 3.5 * collection_diff
        - opp_imminent_threat * urgency * _block_scale
        - wall_overuse_penalty
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
