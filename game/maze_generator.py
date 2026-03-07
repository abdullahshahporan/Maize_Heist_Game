"""
maze_generator.py — Random maze generation with connectivity validation.
"""

import random
from collections import deque

from config import GRID_ROWS, GRID_COLS, TREASURE_VALUES, TREASURE_COUNTS
from game.board import Board, CELL_EMPTY, CELL_PERM_WALL
from game.entities import Player, Treasure


def _bfs_reachable(board: Board, start: tuple, ignore_positions=None):
    """Return set of reachable (r, c) from start using BFS on empty cells.
    ignore_positions: set of (r,c) to treat as walkable even if occupied."""
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in visited and board.in_bounds(nr, nc):
                if board.grid[nr][nc] == CELL_EMPTY:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                elif ignore_positions and (nr, nc) in ignore_positions:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    return visited


def generate_maze(difficulty_key: str):
    """
    Generate a random 12x12 maze, two players, and treasures.
    Returns (board, player1, player2, treasures_list).
    """
    from config import DIFFICULTY_SETTINGS
    wall_density = DIFFICULTY_SETTINGS[difficulty_key]["wall_density"]

    rows, cols = GRID_ROWS, GRID_COLS
    board = Board(rows, cols)

    # Player start positions — top-left area and bottom-right area
    p1_row, p1_col = 1, 1
    p2_row, p2_col = rows - 2, cols - 2

    # Keep borders as walls for a clean look
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                board.set_perm_wall(r, c)

    # Randomly place interior permanent walls
    interior_cells = []
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            interior_cells.append((r, c))

    # Reserve cells around players
    reserved = set()
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            reserved.add((p1_row + dr, p1_col + dc))
            reserved.add((p2_row + dr, p2_col + dc))

    candidates = [pos for pos in interior_cells if pos not in reserved]
    random.shuffle(candidates)
    num_walls = int(len(candidates) * wall_density)

    placed = 0
    for r, c in candidates:
        if placed >= num_walls:
            break
        board.set_perm_wall(r, c)
        # Verify both players are still connected
        reachable = _bfs_reachable(board, (p1_row, p1_col))
        if (p2_row, p2_col) not in reachable:
            board.clear_cell(r, c)  # undo
        else:
            placed += 1

    # Create players
    player1 = Player(1, "Player 1", "minimax", p1_row, p1_col)
    player2 = Player(2, "Player 2", "astar", p2_row, p2_col)

    # Compute reachable empty cells for treasure placement
    reachable = _bfs_reachable(board, (p1_row, p1_col))
    occupied = {(p1_row, p1_col), (p2_row, p2_col)}
    valid_treasure_cells = [pos for pos in reachable if pos not in occupied]

    # Place treasures spread across the board
    # Divide board into quadrants and ensure each gets some treasures
    treasures = []
    treasure_list = []
    for t_type, count in TREASURE_COUNTS.items():
        for _ in range(count):
            treasure_list.append(t_type)
    random.shuffle(treasure_list)

    # Sort valid cells into quadrants for even distribution
    mid_r, mid_c = rows // 2, cols // 2
    quads = [[], [], [], []]  # TL, TR, BL, BR
    for pos in valid_treasure_cells:
        r, c = pos
        qi = (0 if r < mid_r else 2) + (0 if c < mid_c else 1)
        quads[qi].append(pos)
    for q in quads:
        random.shuffle(q)

    # Distribute treasures across quadrants round-robin
    used_positions = set()
    qi = 0
    for t_type in treasure_list:
        placed = False
        for attempt in range(4):
            q = quads[(qi + attempt) % 4]
            for pos in q:
                if pos not in used_positions:
                    r, c = pos
                    treasures.append(
                        Treasure(r, c, t_type, TREASURE_VALUES[t_type])
                    )
                    used_positions.add(pos)
                    placed = True
                    break
            if placed:
                break
        qi = (qi + 1) % 4

    return board, player1, player2, treasures


def find_empty_reachable_cell(board: Board, player_pos: tuple,
                              occupied: set, treasure_positions: set):
    """Find a random reachable empty cell not occupied or holding treasure."""
    reachable = _bfs_reachable(board, player_pos)
    candidates = [
        pos for pos in reachable
        if pos not in occupied and pos not in treasure_positions
        and board.is_empty(*pos)
    ]
    if candidates:
        return random.choice(candidates)
    return None
