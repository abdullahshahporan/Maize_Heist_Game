"""
astar_wall_helper.py — A* based wall placement decision helpers.

Uses A* pathfinding to evaluate how wall placements affect paths
and provides the decision logic for when the A* agent should place walls.
"""

from game.actions import Action, ACTION_PLACE_WALL
from utils.pathfinding import astar, bfs_all_distances
from ai.wall_logic import evaluate_wall_placements

_WALL_BASE_THRESHOLD = 2.5


def _score_opponent_target(treasure, my_dists, opp_dists):
    tp = (treasure.row, treasure.col)
    d_opp = opp_dists.get(tp, 10**9)
    if d_opp == 10**9:
        return float("-inf")

    d_me = my_dists.get(tp, 10**9)
    score = (treasure.value * 2.4) / (d_opp + 1)
    if d_me == 10**9:
        score += treasure.value * 1.6
    else:
        gap = d_me - d_opp
        if gap >= 2:
            score += treasure.value * 1.5
        elif gap >= 0:
            score += treasure.value * 0.8
        elif gap >= -2:
            score += treasure.value * 0.35
        else:
            score -= treasure.value * 0.2
    return score


def find_blocking_wall_on_path(game_state, my_dists, opp_dists):
    """Use A* to find the opponent's path to their nearest treasure,
    then check if we can place a wall that blocks that path.

    Returns (wall_pos, utility) or None if no good blocking wall found.
    """
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    board = game_state.board
    treasures = game_state.treasures

    if not treasures:
        return None

    # Find opponent's most dangerous target: valuable and likely theirs first.
    best_opp_target = None
    best_opp_score = float("-inf")
    for t in treasures:
        target_score = _score_opponent_target(t, my_dists, opp_dists)
        if target_score > best_opp_score:
            best_opp_score = target_score
            best_opp_target = t

    if best_opp_target is None or best_opp_score == float("-inf"):
        return None

    # Get opponent's A* path to their best target
    opp_path = astar(
        board, opponent.pos, best_opp_target.pos,
        blocked_extra={player.pos}
    )
    if not opp_path or len(opp_path) < 2:
        return None

    # Check if any adjacent cell to player lies on the opponent's path
    from game.rules import get_valid_wall_positions
    wall_positions = get_valid_wall_positions(
        board, player, opponent, treasures, game_state.temp_walls,
    )
    if not wall_positions:
        return None

    path_set = set(opp_path[1:])  # exclude opponent's current pos
    best_wall = None
    best_utility = 0.0

    for wp in wall_positions:
        if wp in path_set:
            # This wall directly blocks the opponent's A* path
            utility = best_opp_target.value * 1.5
            # Bonus if it's early in the path (harder to reroute)
            for i, step in enumerate(opp_path):
                if step == wp:
                    utility += max(0, 5 - i) * 0.5
                    break
            d_me = my_dists.get(best_opp_target.pos, 10**9)
            d_opp = opp_dists.get(best_opp_target.pos, 10**9)
            if d_me == 10**9:
                utility += best_opp_target.value * 1.2
            elif d_opp < d_me:
                utility += best_opp_target.value * 0.9
            if utility > best_utility:
                best_utility = utility
                best_wall = wp

    if best_wall is not None:
        return best_wall, best_utility
    return None


def evaluate_walls_with_astar(game_state, my_dists, opp_dists, max_candidates=6):
    """Evaluate wall placements combining BFS-based evaluation with A* path blocking.

    Returns sorted list of ((row, col), utility) tuples.
    """
    # Get standard BFS-based evaluation
    wall_options = evaluate_wall_placements(
        game_state,
        self_dists_before=my_dists,
        opp_dists_before=opp_dists,
        max_candidates=max_candidates,
    )

    # Check A* path blocking bonus
    astar_block = find_blocking_wall_on_path(game_state, my_dists, opp_dists)
    if astar_block is not None:
        block_pos, block_utility = astar_block
        # Merge: if this wall is already in the list, boost it
        found = False
        for i, (pos, util) in enumerate(wall_options):
            if pos == block_pos:
                wall_options[i] = (pos, util + block_utility * 0.5)
                found = True
                break
        if not found:
            wall_options.append((block_pos, block_utility))

    wall_options.sort(key=lambda x: x[1], reverse=True)
    return wall_options


def choose_wall_action(game_state, my_dists, opp_dists, best_move_score):
    """Decide whether to place a wall and which one, using A* enhanced evaluation.

    Returns an Action for wall placement, or None if moving is better.
    """
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()

    wall_options = evaluate_walls_with_astar(
        game_state, my_dists, opp_dists, max_candidates=6,
    )

    if not wall_options:
        return None

    best_wall_pos, best_wall_utility = wall_options[0]

    score_diff = player.score - opponent.score
    wall_threshold = _WALL_BASE_THRESHOLD
    if score_diff < -15:
        wall_threshold = 1.2
    elif score_diff < -5:
        wall_threshold = 1.8
    elif score_diff > 10:
        wall_threshold = 3.5

    if (best_wall_utility > wall_threshold
            and best_wall_utility > 0.06 * best_move_score):
        return Action(ACTION_PLACE_WALL, best_wall_pos)

    return None
