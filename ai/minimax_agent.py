"""
minimax_agent.py — AI Agent 1: Minimax with Alpha-Beta pruning.
Optimized: move ordering at root, transposition table reuse, iterative
deepening for time control at higher depths.
"""

from config import DIFFICULTY_SETTINGS
from game.actions import Action, ACTION_MOVE
from ai.alphabeta import alphabeta, clear_transposition_table, _order_actions


def choose_action_minimax(game_state, difficulty: str) -> Action:
    """
    Evaluate all legal actions for the current player using Minimax
    with Alpha-Beta pruning and return the best action.
    Uses iterative deepening so the TT from shallower searches
    improves pruning at deeper levels.
    """
    depth = DIFFICULTY_SETTINGS[difficulty]["minimax_depth"]
    player = game_state.get_current_player()
    actions = game_state.get_all_actions()

    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]  # only one choice — skip search

    # Order moves at root for better pruning
    actions = _order_actions(actions, game_state)

    clear_transposition_table()

    best_action = actions[0]

    # Iterative deepening: search depth 1, 2, ... up to target
    # Each pass fills the TT, making deeper passes prune more aggressively
    for d in range(1, depth + 1):
        current_best_action = actions[0]
        current_best_value = float('-inf')

        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            value = alphabeta(child, d - 1, float('-inf'), float('inf'),
                              False, player.id)
            if value > current_best_value:
                current_best_value = value
                current_best_action = action

        best_action = current_best_action

        # Re-order actions: put current best first for next iteration
        if best_action in actions:
            actions.remove(best_action)
            actions.insert(0, best_action)

        # Early termination if we found a winning move
        if current_best_value >= 9000.0:
            break

    return best_action
