"""
board.py — Board representation and cell queries.
"""

from config import GRID_ROWS, GRID_COLS


# Cell types stored in the grid
CELL_EMPTY = 0
CELL_PERM_WALL = 1
CELL_TEMP_WALL = 2


class Board:
    """12x12 grid that tracks permanent/temporary wall layout."""

    def __init__(self, rows: int = GRID_ROWS, cols: int = GRID_COLS):
        self.rows = rows
        self.cols = cols
        # 2-D list: 0 = empty, 1 = permanent wall, 2 = temp wall
        self.grid = [[CELL_EMPTY] * cols for _ in range(rows)]

    # ── queries ─────────────────────────────────────────
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_empty(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == CELL_EMPTY

    def is_perm_wall(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == CELL_PERM_WALL

    def is_temp_wall(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == CELL_TEMP_WALL

    def is_wall(self, r: int, c: int) -> bool:
        return self.is_perm_wall(r, c) or self.is_temp_wall(r, c)

    def set_perm_wall(self, r: int, c: int):
        self.grid[r][c] = CELL_PERM_WALL

    def set_temp_wall(self, r: int, c: int):
        self.grid[r][c] = CELL_TEMP_WALL

    def clear_cell(self, r: int, c: int):
        self.grid[r][c] = CELL_EMPTY

    def clone(self):
        b = Board(self.rows, self.cols)
        b.grid = [row[:] for row in self.grid]
        return b

    def walkable_neighbors(self, r: int, c: int):
        """Return list of (nr, nc) neighbors that are empty."""
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc) and self.grid[nr][nc] == CELL_EMPTY:
                result.append((nr, nc))
        return result
