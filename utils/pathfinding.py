"""
pathfinding.py — A* shortest-path and BFS utilities used by AI agents.
Optimized for heavy use inside minimax search trees.
"""

import heapq
from collections import deque
from game.board import Board, CELL_EMPTY

# Pre-computed direction offsets (avoid re-creating tuples each call)
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def manhattan(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(board: Board, start: tuple, goal: tuple,
          blocked_extra: set = None) -> list:
    """
    A* search on the board grid.
    Returns list of (row, col) from start to goal (inclusive), or [] if
    no path exists.  blocked_extra is an optional set of positions to
    treat as impassable in addition to walls.
    """
    if start == goal:
        return [start]

    grid = board.grid
    rows = board.rows
    cols = board.cols
    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    _heappush = heapq.heappush
    _heappop = heapq.heappop

    while open_set:
        _f, cost, current = _heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        # Skip stale entries
        if cost > g_score.get(current, float('inf')):
            continue

        cr, cc = current
        tentative_g = cost + 1
        for dr, dc in _DIRS:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == CELL_EMPTY:
                neighbor = (nr, nc)
                if blocked_extra and neighbor in blocked_extra:
                    continue
                if tentative_g < g_score.get(neighbor, 999999):
                    g_score[neighbor] = tentative_g
                    came_from[neighbor] = current
                    _heappush(open_set, (tentative_g + manhattan(neighbor, goal),
                                         tentative_g, neighbor))

    return []  # no path


def bfs_distance(board: Board, start: tuple, goal: tuple,
                 blocked_extra: set = None) -> int:
    """BFS distance between two cells. Returns -1 if unreachable."""
    if start == goal:
        return 0

    grid = board.grid
    rows = board.rows
    cols = board.cols
    visited = {start}
    queue = deque()
    queue.append((start[0], start[1], 0))

    while queue:
        r, c, dist = queue.popleft()
        next_dist = dist + 1
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if nr == goal[0] and nc == goal[1]:
                return next_dist
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = (nr, nc)
                if nb not in visited and grid[nr][nc] == CELL_EMPTY:
                    if not (blocked_extra and nb in blocked_extra):
                        visited.add(nb)
                        queue.append((nr, nc, next_dist))
    return -1


def bfs_all_distances(board: Board, start: tuple,
                      blocked_extra: set = None) -> dict:
    """BFS from start, return dict {(r,c): distance} for all reachable cells."""
    grid = board.grid
    rows = board.rows
    cols = board.cols
    visited = {start: 0}
    queue = deque()
    queue.append((start[0], start[1], 0))

    while queue:
        r, c, dist = queue.popleft()
        next_dist = dist + 1
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = (nr, nc)
                if nb not in visited and grid[nr][nc] == CELL_EMPTY:
                    if not (blocked_extra and nb in blocked_extra):
                        visited[nb] = next_dist
                        queue.append((nr, nc, next_dist))
    return visited


def bfs_distance_from_grid(grid, rows: int, cols: int,
                           start: tuple, goal: tuple) -> int:
    """Lightweight BFS using raw grid — no Board object needed.
    Used by wall_logic to avoid constructing Board clones."""
    if start == goal:
        return 0
    visited = {start}
    queue = deque()
    queue.append((start[0], start[1], 0))

    while queue:
        r, c, dist = queue.popleft()
        next_dist = dist + 1
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if nr == goal[0] and nc == goal[1] and grid[nr][nc] == CELL_EMPTY:
                return next_dist
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = (nr, nc)
                if nb not in visited and grid[nr][nc] == CELL_EMPTY:
                    visited.add(nb)
                    queue.append((nr, nc, next_dist))
    return -1
