"""
tactical_blocker.py — Wall evaluation helpers for the A* agent.

Helpers:
- chokepoint_score: measures how much a wall reduces opponent mobility
- opponent_cutoff_bonus: detects when a wall blocks opponent from treasures
- race_impact: evaluates how a wall shifts BFS race advantage
- evaluate_wall_placements: ranks candidate wall positions by utility
"""

from game.board import CELL_EMPTY, CELL_TEMP_WALL
from game.rules import get_valid_wall_positions
from utils.pathfinding import bfs_all_distances, bfs_distance_from_grid


_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# ── helper: chokepoint detection ──────────────────────
def chokepoint_score(grid, rows, cols, wall_pos, opponent_pos):
    """How much placing a wall at wall_pos restricts opponent movement.

    Returns a score >= 0.  Higher = more restrictive for the opponent.
    Considers:
      - direct adjacency to opponent (wall next to opponent blocks a move)
      - number of adjacent walls (corridor-forming potential)
    """
    wr, wc = wall_pos
    opr, opc = opponent_pos
    score = 0.0

    # Direct block: wall is adjacent to opponent → removes one of their moves
    if abs(wr - opr) + abs(wc - opc) == 1:
        score += 3.0

    # Corridor formation: more adjacent walls → tighter passage
    adj_walls = 0
    for dr, dc in _DIRS:
        nr, nc = wr + dr, wc + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if grid[nr][nc] != CELL_EMPTY:
                adj_walls += 1
    score += adj_walls * 0.8
    return score


# ── helper: opponent cutoff detection ─────────────────
def opponent_cutoff_bonus(opp_dist_before, opp_dist_after, treasure_value):
    """Bonus when a wall makes a treasure much harder or impossible for opponent.

    opp_dist_before / opp_dist_after: BFS distance (or -1 if unreachable).
    Returns a bonus >= 0.
    """
    if opp_dist_before < 0:
        return 0.0  # opponent couldn't reach it before either
    if opp_dist_after < 0:
        # completely cut off — massive bonus
        return treasure_value * 3.0
    increase = opp_dist_after - opp_dist_before
    if increase >= 4:
        return treasure_value * 1.5
    if increase >= 2:
        return treasure_value * 0.6
    return 0.0


# ── helper: race impact across treasures ──────────────
def race_impact(treasures, self_dists_before, opp_dists_before,
                self_dists_after, opp_dists_after):
    """Aggregate how a wall shifts the BFS race for all treasures.

    Returns (opp_delay, self_penalty) weighted by treasure value.
    """
    opp_delay = 0.0
    self_penalty = 0.0
    for t in treasures:
        tp = (t.row, t.col)
        w = t.value * 0.18

        d_opp_b = opp_dists_before.get(tp, -1)
        d_opp_a = opp_dists_after.get(tp, -1) if opp_dists_after is not None else -1
        d_self_b = self_dists_before.get(tp, -1)
        d_self_a = self_dists_after.get(tp, -1) if self_dists_after is not None else -1

        if d_opp_b >= 0:
            if d_opp_a >= 0:
                opp_delay += max(0, d_opp_a - d_opp_b) * w
            else:
                opp_delay += 10.0 * w  # cut off

        if d_self_b >= 0:
            if d_self_a >= 0:
                self_penalty += max(0, d_self_a - d_self_b) * w
            else:
                self_penalty += 15.0 * w  # self-cutoff is very bad
    return opp_delay, self_penalty


# ── helper: score treasure importance for shortlisting ─
def _score_treasure_importance(treasure, self_dists, opp_dists):
    tp = (treasure.row, treasure.col)
    d_me = self_dists.get(tp, 10**9)
    d_opp = opp_dists.get(tp, 10**9)
    if d_opp == 10**9:
        return 0.0
    contested = 1.0 if abs(d_me - d_opp) <= 3 else 0.4
    return treasure.value * contested / (d_opp + 1)


# ── helper: shortlist best wall candidates ────────────
def _shortlist_wall_positions(wall_positions, treasures, self_dists,
                              opp_dists, opp_pos, grid, rows, cols,
                              max_candidates):
    if len(wall_positions) <= max_candidates:
        return wall_positions

    important = sorted(
        treasures,
        key=lambda t: _score_treasure_importance(t, self_dists, opp_dists),
        reverse=True,
    )[:5]

    ranked = []
    for wr, wc in wall_positions:
        score = 0.0
        # Proximity to contested treasures
        for t in important:
            d_t = abs(wr - t.row) + abs(wc - t.col)
            if d_t <= 2:
                score += t.value * 2.5
            elif d_t <= 4:
                score += t.value * 0.8
        # Chokepoint potential
        score += chokepoint_score(grid, rows, cols, (wr, wc), opp_pos)
        ranked.append((score, (wr, wc)))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [pos for _, pos in ranked[:max_candidates]]


def evaluate_wall_placements(game_state, self_dists_before=None,
                             opp_dists_before=None, max_candidates=8):
    """Evaluate and rank wall placements by tactical utility.

    Uses chokepoint_score, opponent_cutoff_bonus, and race_impact helpers
    to produce a combined utility for each candidate wall position.
    """
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board
    treasures = game_state.treasures

    wall_positions = get_valid_wall_positions(
        board, player, opponent, treasures, game_state.temp_walls,
    )
    if not wall_positions or not treasures:
        return []

    if opp_dists_before is None:
        opp_dists_before = bfs_all_distances(board, opponent.pos)
    if self_dists_before is None:
        self_dists_before = bfs_all_distances(board, player.pos)

    grid = board.grid
    rows = board.rows
    cols = board.cols

    wall_positions = _shortlist_wall_positions(
        wall_positions, treasures, self_dists_before, opp_dists_before,
        opponent.pos, grid, rows, cols, max_candidates,
    )

    # Use top 5 most important treasures for detailed evaluation
    important_treasures = sorted(
        treasures,
        key=lambda t: _score_treasure_importance(t, self_dists_before, opp_dists_before),
        reverse=True,
    )[:5]

    results = []

    for wr, wc in wall_positions:
        # Temporarily place wall
        grid[wr][wc] = CELL_TEMP_WALL

        # 1) Chokepoint value
        choke = chokepoint_score(grid, rows, cols, (wr, wc), opponent.pos)

        # 2) Race impact on important treasures
        opp_delay = 0.0
        self_penalty = 0.0
        cutoff = 0.0
        for t in important_treasures:
            tp = (t.row, t.col)
            w = t.value * 0.18

            d_opp_b = opp_dists_before.get(tp, -1)
            d_self_b = self_dists_before.get(tp, -1)
            d_opp_a = bfs_distance_from_grid(grid, rows, cols, opponent.pos, tp)
            d_self_a = bfs_distance_from_grid(grid, rows, cols, player.pos, tp)

            # Opponent delay
            if d_opp_b >= 0:
                if d_opp_a >= 0:
                    opp_delay += max(0, d_opp_a - d_opp_b) * w
                else:
                    opp_delay += 10.0 * w

            # Self penalty
            if d_self_b >= 0:
                if d_self_a >= 0:
                    self_penalty += max(0, d_self_a - d_self_b) * w
                else:
                    self_penalty += 15.0 * w

            # Cutoff bonus
            cutoff += opponent_cutoff_bonus(d_opp_b, d_opp_a, t.value)

        # Remove temporary wall
        grid[wr][wc] = CELL_EMPTY

        utility = opp_delay - self_penalty + choke + cutoff
        results.append(((wr, wc), utility))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
