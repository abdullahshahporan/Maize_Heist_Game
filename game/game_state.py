"""
game_state.py — Central game state used by game loop, AI, and UI.
Optimized clone() and apply_action() for fast AI search.
"""

import random
from config import (MAX_TURNS, TEMP_WALL_LIFETIME, TREASURE_VALUES,
                    GRID_ROWS, GRID_COLS)
from game.board import Board, CELL_TEMP_WALL, CELL_EMPTY
from game.entities import Player, Treasure, TemporaryWall
from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from game.rules import (get_valid_moves, get_valid_wall_positions,
                         get_all_actions, has_any_valid_action)
from utils.pathfinding import bfs_distance
from game.maze_generator import find_empty_reachable_cell


class GameState:
    """
    Full snapshot of the game at any moment.
    Supports cloning for AI search trees.
    """
    __slots__ = ('board', 'player1', 'player2', 'treasures', 'temp_walls',
                 'current_player_index', 'turn_count', 'round_count',
                 'game_mode', 'difficulty', 'game_over', 'winner',
                 'end_reason', 'wall_placements', '_is_simulation',
                 '_logged', '_ab_tt_key', '_cached_actions',
                 '_distance_cache', '_treasure_value_map',
                 'last_action', 'last_action_player_id')

    def __init__(self, board: Board, player1: Player, player2: Player,
                 treasures: list, game_mode: str, difficulty: str):
        self.board = board
        self.player1 = player1
        self.player2 = player2
        self.treasures = list(treasures)
        self.temp_walls: list = []

        self.current_player_index = 0   # 0 → player1, 1 → player2
        self.turn_count = 0
        self.round_count = 0

        self.game_mode = game_mode
        self.difficulty = difficulty
        self.game_over = False
        self.winner = None
        self.end_reason = ""

        self.wall_placements = {1: 0, 2: 0}
        self._is_simulation = False  # True for AI clones — skips spawning
        self._logged = False
        self._ab_tt_key = None
        self._cached_actions = None
        self._distance_cache = {}
        self._treasure_value_map = None
        self.last_action = None
        self.last_action_player_id = None

    # ── Player accessors ────────────────────────────────
    def get_current_player(self) -> Player:
        return self.player1 if self.current_player_index == 0 else self.player2

    def get_opponent(self) -> Player:
        return self.player2 if self.current_player_index == 0 else self.player1

    # ── Action helpers ──────────────────────────────────
    def get_valid_moves(self, player: Player):
        opponent = self.player2 if player.id == 1 else self.player1
        return get_valid_moves(self.board, player, opponent)

    def get_valid_wall_positions(self, player: Player):
        opponent = self.player2 if player.id == 1 else self.player1
        return get_valid_wall_positions(self.board, player, opponent,
                                        self.treasures, self.temp_walls)

    def get_all_actions(self, player: Player = None):
        if player is None:
            if self._cached_actions is not None:
                return list(self._cached_actions)
            player = self.get_current_player()
        opponent = self.player2 if player.id == 1 else self.player1
        actions = get_all_actions(self.board, player, opponent, self.treasures,
                                  self.temp_walls)
        if player is self.get_current_player():
            self._cached_actions = tuple(actions)
        return actions

    def get_treasure_value_map(self):
        if self._treasure_value_map is None:
            self._treasure_value_map = {
                (treasure.row, treasure.col): treasure.value
                for treasure in self.treasures
            }
        return self._treasure_value_map

    def _invalidate_caches(self):
        self._ab_tt_key = None
        self._cached_actions = None
        self._distance_cache.clear()
        self._treasure_value_map = None

    # ── Apply action ────────────────────────────────────
    def apply_action(self, action: Action):
        """Apply action for current player, advance turn, handle round end."""
        player = self.get_current_player()

        # Track last action for UI highlighting
        if not self._is_simulation:
            self.last_action = action
            self.last_action_player_id = player.id

        if action.action_type == ACTION_MOVE:
            player.row, player.col = action.target
            self._collect_treasure_if_present(player)
        elif action.action_type == ACTION_PLACE_WALL:
            r, c = action.target
            self.board.set_temp_wall(r, c)
            # In real game (not AI simulation), verify opponent isn't
            # completely cut off from all treasures
            wall_ok = True
            if not self._is_simulation:
                opp = self.get_opponent()
                opp_has_path = False
                for t in self.treasures:
                    d = bfs_distance(self.board, opp.pos, t.pos)
                    if d >= 0:
                        opp_has_path = True
                        break
                if not opp_has_path:
                    self.board.clear_cell(r, c)
                    wall_ok = False
            if wall_ok:
                tw = TemporaryWall(r, c, player.id, self.round_count,
                                   TEMP_WALL_LIFETIME)
                self.temp_walls.append(tw)
                self.wall_placements[player.id] += 1

        self.turn_count += 1

        # Full round completed when player 2 just acted
        if self.current_player_index == 1:
            self.round_count += 1
            self._update_temporary_walls()

        # Switch turn
        self.current_player_index = 1 - self.current_player_index
        self._invalidate_caches()

        # Check terminal conditions
        self._check_terminal()

    def _collect_treasure_if_present(self, player: Player):
        """If the player is standing on a treasure, collect it."""
        pr, pc = player.row, player.col
        for i, t in enumerate(self.treasures):
            if t.row == pr and t.col == pc:
                player.score += t.value
                player.collected_count += 1
                # Fast removal by index
                self.treasures[i] = self.treasures[-1]
                self.treasures.pop()
                # Only spawn new treasures in real game, not AI simulations
                if not self._is_simulation:
                    self._spawn_treasure()
                break

    def _spawn_treasure(self):
        """Spawn one new treasure at a random reachable empty cell."""
        occupied = {self.player1.pos, self.player2.pos}
        treasure_positions = {t.pos for t in self.treasures}
        cell = find_empty_reachable_cell(self.board,
                                         self.player1.pos,
                                         occupied, treasure_positions)
        if cell:
            roll = random.random()
            if roll < 0.5:
                t_type = "cash"
            elif roll < 0.85:
                t_type = "gold"
            else:
                t_type = "diamond"
            self.treasures.append(
                Treasure(cell[0], cell[1], t_type, TREASURE_VALUES[t_type])
            )

    def _update_temporary_walls(self):
        """Decrement lifetime of all temp walls; remove expired ones."""
        remaining = []
        for tw in self.temp_walls:
            tw.remaining_rounds -= 1
            if tw.remaining_rounds <= 0:
                self.board.grid[tw.row][tw.col] = CELL_EMPTY  # inline clear
            else:
                remaining.append(tw)
        self.temp_walls = remaining

    # ── Terminal checks ─────────────────────────────────
    def _check_terminal(self):
        if self.game_over:
            return

        if self.turn_count >= MAX_TURNS:
            self.game_over = True
            self._determine_winner_by_score("Turn limit reached")
            return

        cp = self.get_current_player()
        opp = self.get_opponent()
        if not has_any_valid_action(self.board, cp, opp, self.treasures):
            self.game_over = True
            self.winner = opp
            self.end_reason = f"{cp.name} has no valid action"

    def _determine_winner_by_score(self, reason: str):
        self.end_reason = reason
        if self.player1.score > self.player2.score:
            self.winner = self.player1
        elif self.player2.score > self.player1.score:
            self.winner = self.player2
        else:
            self.winner = None

    def is_terminal(self) -> bool:
        return self.game_over

    def determine_winner(self):
        """Force winner determination (called at game end)."""
        if self.winner is None and not self.end_reason:
            self._determine_winner_by_score("Game ended")

    # ── Deep clone for AI search (optimized) ────────────
    def clone(self):
        """Lightweight clone optimized for AI search trees."""
        b = Board.__new__(Board)
        b.rows = self.board.rows
        b.cols = self.board.cols
        b.grid = [row[:] for row in self.board.grid]

        p1 = Player.__new__(Player)
        p1.id = self.player1.id
        p1.name = self.player1.name
        p1.type = self.player1.type
        p1.row = self.player1.row
        p1.col = self.player1.col
        p1.score = self.player1.score
        p1.collected_count = self.player1.collected_count

        p2 = Player.__new__(Player)
        p2.id = self.player2.id
        p2.name = self.player2.name
        p2.type = self.player2.type
        p2.row = self.player2.row
        p2.col = self.player2.col
        p2.score = self.player2.score
        p2.collected_count = self.player2.collected_count

        gs = GameState.__new__(GameState)
        gs.board = b
        gs.player1 = p1
        gs.player2 = p2
        gs.treasures = [t.clone() for t in self.treasures]
        gs.temp_walls = [tw.clone() for tw in self.temp_walls]
        gs.current_player_index = self.current_player_index
        gs.turn_count = self.turn_count
        gs.round_count = self.round_count
        gs.game_mode = self.game_mode
        gs.difficulty = self.difficulty
        gs.game_over = self.game_over
        gs.winner = None
        gs.end_reason = self.end_reason
        gs.wall_placements = {1: self.wall_placements[1],
                               2: self.wall_placements[2]}
        gs._is_simulation = True  # AI clones skip spawning
        gs._logged = False
        gs._ab_tt_key = None
        gs._cached_actions = None
        gs._distance_cache = {}
        gs._treasure_value_map = None
        gs.last_action = None
        gs.last_action_player_id = None
        return gs
