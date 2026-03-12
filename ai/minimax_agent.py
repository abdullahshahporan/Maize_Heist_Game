"""
minimax_agent.py — Aggressive Minimax + Alpha-Beta driver.

Design:
- Instant-capture at value >= 5 (cash and above — never miss free points)
- Urgency: searches deeper (+1) when falling behind
- Tighter aspiration windows for faster convergence
- Iterative deepening with TT reuse across depths
"""

from config import DIFFICULTY_SETTINGS
from game.actions import ACTION_MOVE
from ai.alphabeta import alphabeta, clear_transposition_table, _order_actions


ASPIRATION_BASE = 20.0


def choose_action_minimax(game_state, difficulty):
    depth = DIFFICULTY_SETTINGS[difficulty]["minimax_depth"]
    player = game_state.get_current_player()
    opponent = game_state.get_opponent()
    actions = game_state.get_all_actions()

    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]

    # ── Urgency: search deeper when behind ────────────
    score_diff = player.score - opponent.score
    if score_diff < -10:
        depth = min(depth + 1, 6)

    if len(actions) <= 3 or len(game_state.treasures) <= 4:
        depth = min(depth + 1, 7)

    treasure_values = game_state.get_treasure_value_map()
    best_capture = None
    best_capture_val = 0
    for action in actions:
        if action.action_type == ACTION_MOVE:
            value = treasure_values.get(action.target, 0)
            if value > best_capture_val:
                best_capture_val = value
                best_capture = action

    # Instant-capture any treasure (cash=5+) — never miss free points
    if best_capture and best_capture_val >= 5:
        return best_capture

    actions = _order_actions(actions, game_state)
    clear_transposition_table()

    root_children = []
    for action in actions:
        child = game_state.clone()
        child.apply_action(action)
        root_children.append((action, child))

    best_action = actions[0]
    prev_value = 0.0

    for current_depth in range(1, depth + 1):
        if current_depth >= 2:
            window = ASPIRATION_BASE + current_depth * 2.5
            alpha = prev_value - window
            beta = prev_value + window
        else:
            alpha = float("-inf")
            beta = float("inf")

        current_best_action = actions[0]
        current_best_value = float("-inf")

        for action, child in root_children:
            value = alphabeta(child, current_depth - 1, alpha, beta, False, player.id)
            if value > current_best_value:
                current_best_value = value
                current_best_action = action

        if current_best_value <= alpha or current_best_value >= beta:
            current_best_value = float("-inf")
            for action, child in root_children:
                value = alphabeta(child, current_depth - 1, float("-inf"), float("inf"), False, player.id)
                if value > current_best_value:
                    current_best_value = value
                    current_best_action = action

        best_action = current_best_action
        prev_value = current_best_value

        if best_action != root_children[0][0]:
            for index, (action, child) in enumerate(root_children):
                if action == best_action:
                    root_children.insert(0, root_children.pop(index))
                    break

        if current_best_value >= 9000.0:
            break

    return best_action
