"""
rules.py — Validation helpers shared by human and AI players.
Optimized: set-based treasure lookup, early-exit checks.
"""

from game.board import Board, CELL_EMPTY
from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from config import MAX_WALLS_PER_PLAYER

# Pre-computed direction offsets
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _treasure_positions_set(treasures) -> frozenset:
    """Build a set of (row, col) from a treasure list for O(1) lookup."""
    return frozenset((t.row, t.col) for t in treasures)


def get_valid_moves(board: Board, player, opponent) -> list:
    """Return list of (row, col) the player can move to."""
    moves = []
    pr, pc = player.row, player.col
    opr, opc = opponent.row, opponent.col
    grid = board.grid
    rows, cols = board.rows, board.cols
    for dr, dc in _DIRS:
        nr, nc = pr + dr, pc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)):
            moves.append((nr, nc))
    return moves


def get_valid_wall_positions(board: Board, player, opponent, treasures,
                             temp_walls=None) -> list:
    """Return list of (row, col) where the player can place a temp wall.
    Enforces MAX_WALLS_PER_PLAYER limit on active walls."""
    # Check active wall count limit
    if temp_walls is not None:
        active = sum(1 for tw in temp_walls if tw.owner_id == player.id)
        if active >= MAX_WALLS_PER_PLAYER:
            return []

    t_set = _treasure_positions_set(treasures)
    positions = []
    pr, pc = player.row, player.col
    opr, opc = opponent.row, opponent.col
    grid = board.grid
    rows, cols = board.rows, board.cols
    for dr, dc in _DIRS:
        nr, nc = pr + dr, pc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)
                and (nr, nc) not in t_set):
            positions.append((nr, nc))
    return positions


def get_all_actions(board, player, opponent, treasures,
                    temp_walls=None) -> list:
    """Return list of Action objects the player can perform this turn.
    Move actions are returned first (better for alpha-beta ordering).
    Respects MAX_WALLS_PER_PLAYER limit."""
    actions = []
    pr, pc = player.row, player.col
    opr, opc = opponent.row, opponent.col
    grid = board.grid
    rows, cols = board.rows, board.cols
    t_set = _treasure_positions_set(treasures)

    for dr, dc in _DIRS:
        nr, nc = pr + dr, pc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)):
            actions.append(Action(ACTION_MOVE, (nr, nc)))

    # Check wall limit before generating wall actions
    wall_allowed = True
    if temp_walls is not None:
        active = sum(1 for tw in temp_walls if tw.owner_id == player.id)
        wall_allowed = active < MAX_WALLS_PER_PLAYER

    if wall_allowed:
        for dr, dc in _DIRS:
            nr, nc = pr + dr, pc + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] == CELL_EMPTY
                    and not (nr == opr and nc == opc)
                    and (nr, nc) not in t_set):
                actions.append(Action(ACTION_PLACE_WALL, (nr, nc)))

    return actions


def has_any_valid_action(board, player, opponent, treasures) -> bool:
    """True if the player can do at least one action. Stops at first found."""
    pr, pc = player.row, player.col
    opr, opc = opponent.row, opponent.col
    grid = board.grid
    rows, cols = board.rows, board.cols

    for dr, dc in _DIRS:
        nr, nc = pr + dr, pc + dc
        if (0 <= nr < rows and 0 <= nc < cols
                and grid[nr][nc] == CELL_EMPTY
                and not (nr == opr and nc == opc)):
            return True  # at least one move exists — done
    return False
