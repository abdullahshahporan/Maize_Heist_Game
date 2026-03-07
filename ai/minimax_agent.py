"""
minimax_agent.py — AI Agent 1: Minimax with Alpha-Beta pruning.
Optimized: iterative deepening with aspiration windows, TT reuse
across iterations, instant-capture shortcut.
"""

from config import DIFFICULTY_SETTINGS
from game.actions import Action, ACTION_MOVE
from ai.alphabeta import alphabeta, clear_transposition_table, _order_actions


def choose_action_minimax(game_state, difficulty: str) -> Action:
    """
    Evaluate all legal actions using Minimax with Alpha-Beta pruning.
    Uses iterative deepening with aspiration windows so shallow-depth
    TT entries accelerate deeper searches.
    """
    depth = DIFFICULTY_SETTINGS[difficulty]["minimax_depth"]
    player = game_state.get_current_player()
    actions = game_state.get_all_actions()

    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]

    # ── Instant-capture shortcut ────────────────────────
    # If a move lands on a treasure, take it immediately (no search cost).
    treasure_set = {(t.row, t.col): t.value for t in game_state.treasures}
    best_capture = None
    best_capture_val = 0
    for a in actions:
        if a.action_type == ACTION_MOVE and a.target in treasure_set:
            v = treasure_set[a.target]
            if v > best_capture_val:
                best_capture_val = v
                best_capture = a
    # Only skip search for high-value captures (gold/diamond)
    if best_capture and best_capture_val >= 10:
        return best_capture

    # Order moves at root for better pruning
    actions = _order_actions(actions, game_state)

    clear_transposition_table()

    best_action = actions[0]
    prev_value = 0.0
    ASPIRATION_WINDOW = 30.0

    # Iterative deepening with aspiration windows
    for d in range(1, depth + 1):
        # Aspiration window — narrows search on iterations 2+
        if d >= 2:
            a_alpha = prev_value - ASPIRATION_WINDOW
            a_beta = prev_value + ASPIRATION_WINDOW
        else:
            a_alpha = float('-inf')
            a_beta = float('inf')

        current_best_action = actions[0]
        current_best_value = float('-inf')

        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            value = alphabeta(child, d - 1, a_alpha, a_beta,
                              False, player.id)
            if value > current_best_value:
                current_best_value = value
                current_best_action = action

        # If aspiration window failed (all values outside), re-search
        if current_best_value <= a_alpha or current_best_value >= a_beta:
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
        prev_value = current_best_value

        # Put best first for next iteration
        if best_action in actions:
            actions.remove(best_action)
            actions.insert(0, best_action)

        if current_best_value >= 9000.0:
            break

    return best_action
