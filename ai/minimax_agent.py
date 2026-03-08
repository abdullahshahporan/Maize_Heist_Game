"""
minimax_agent.py — Root driver for Minimax + Alpha-Beta.

Changes:
- keeps iterative deepening
- reuses TT across iterative depths
- slightly stronger treasure-first shortcut
- narrower aspiration window growth
"""

from config import DIFFICULTY_SETTINGS
from game.actions import ACTION_MOVE
from ai.alphabeta import alphabeta, clear_transposition_table, _order_actions


ASPIRATION_BASE = 24.0


def choose_action_minimax(game_state, difficulty):
    depth = DIFFICULTY_SETTINGS[difficulty]["minimax_depth"]
    player = game_state.get_current_player()
    actions = game_state.get_all_actions()

    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]

    treasure_values = {(t.row, t.col): t.value for t in game_state.treasures}
    best_capture = None
    best_capture_val = 0
    for action in actions:
        if action.action_type == ACTION_MOVE:
            value = treasure_values.get(action.target, 0)
            if value > best_capture_val:
                best_capture_val = value
                best_capture = action

    # Instant-capture gold/diamond — always take high-value treasures.
    if best_capture and best_capture_val >= 10:
        return best_capture

    actions = _order_actions(actions, game_state)
    clear_transposition_table()

    best_action = actions[0]
    prev_value = 0.0

    for current_depth in range(1, depth + 1):
        if current_depth >= 2:
            window = ASPIRATION_BASE + current_depth * 3.0
            alpha = prev_value - window
            beta = prev_value + window
        else:
            alpha = float("-inf")
            beta = float("inf")

        current_best_action = actions[0]
        current_best_value = float("-inf")

        for action in actions:
            child = game_state.clone()
            child.apply_action(action)
            value = alphabeta(child, current_depth - 1, alpha, beta, False, player.id)
            if value > current_best_value:
                current_best_value = value
                current_best_action = action

        if current_best_value <= alpha or current_best_value >= beta:
            current_best_value = float("-inf")
            for action in actions:
                child = game_state.clone()
                child.apply_action(action)
                value = alphabeta(child, current_depth - 1, float("-inf"), float("inf"), False, player.id)
                if value > current_best_value:
                    current_best_value = value
                    current_best_action = action

        best_action = current_best_action
        prev_value = current_best_value

        if best_action in actions:
            actions.remove(best_action)
            actions.insert(0, best_action)

        if current_best_value >= 9000.0:
            break

    return best_action
