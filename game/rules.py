"""
rules.py — Validation helpers shared by human and AI players.
Optimized: set-based treasure lookup, early-exit checks.
"""

from game.board import Board, CELL_EMPTY
from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL

# Pre-computed direction offsets
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _treasure_positions_set(treasures) -> frozenset:
    """Build a set of (row, col) from a treasure list for O(1) lookup."""
    return frozenset((t.row, t.col) for t in treasures)


def is_valid_move(board: Board, player, opponent, target: tuple) -> bool:
    """Check if a player can move to target (row, col)."""
    r, c = target
    if not (0 <= r < board.rows and 0 <= c < board.cols):
        return False
    if board.grid[r][c] != CELL_EMPTY:
        return False
    if r == opponent.row and c == opponent.col:
        return False
    # Must be adjacent (1 cell away, cardinal)
    if abs(r - player.row) + abs(c - player.col) != 1:
        return False
    return True


def is_valid_wall_placement(board: Board, player, opponent,
                            target: tuple, treasure_set: frozenset) -> bool:
    """Check if player can place a temporary wall at target.
    treasure_set must be a frozenset of (row, col) for O(1) lookup."""
    r, c = target
    if not (0 <= r < board.rows and 0 <= c < board.cols):
        return False
    if board.grid[r][c] != CELL_EMPTY:
        return False
    if abs(r - player.row) + abs(c - player.col) != 1:
        return False
    if r == opponent.row and c == opponent.col:
        return False
    if (r, c) in treasure_set:
        return False
    return True


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


def get_valid_wall_positions(board: Board, player, opponent, treasures) -> list:
    """Return list of (row, col) where the player can place a temp wall."""
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


def get_all_actions(board, player, opponent, treasures) -> list:
    """Return list of Action objects the player can perform this turn.
    Move actions are returned first (better for alpha-beta ordering)."""
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
