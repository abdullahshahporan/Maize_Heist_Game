"""
input_handler.py — Handles keyboard/mouse input for the human player.
"""

import pygame
from game.actions import Action, ACTION_MOVE, ACTION_PLACE_WALL
from game.rules import get_valid_moves, get_valid_wall_positions
from ui.renderer import cell_from_pixel


class HumanInputHandler:
    """
    Manages human player input during their turn.
    Supports arrow-key / WASD movement and wall placement mode (E key).
    """

    def __init__(self):
        self.wall_mode = False
        self.wall_highlights = []

    def reset(self):
        self.wall_mode = False
        self.wall_highlights = []

    def enter_wall_mode(self, game_state):
        """Activate wall placement mode and compute valid positions."""
        player = game_state.get_current_player()
        opponent = game_state.get_opponent()
        self.wall_highlights = get_valid_wall_positions(
            game_state.board, player, opponent, game_state.treasures
        )
        if self.wall_highlights:
            self.wall_mode = True
        # If no valid wall positions, stay in move mode

    def handle_event(self, event, game_state) -> Action | None:
        """
        Process a single pygame event.
        Returns an Action if the human chose one, else None.
        """
        player = game_state.get_current_player()
        opponent = game_state.get_opponent()

        if event.type == pygame.KEYDOWN:
            # Toggle wall mode
            if event.key == pygame.K_e:
                if self.wall_mode:
                    self.wall_mode = False
                    self.wall_highlights = []
                else:
                    self.enter_wall_mode(game_state)
                return None

            # Cancel wall mode
            if event.key == pygame.K_ESCAPE:
                self.wall_mode = False
                self.wall_highlights = []
                return None

            # Movement keys
            if not self.wall_mode:
                direction = None
                if event.key in (pygame.K_UP, pygame.K_w):
                    direction = (-1, 0)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    direction = (1, 0)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    direction = (0, -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    direction = (0, 1)

                if direction:
                    target = (player.row + direction[0],
                              player.col + direction[1])
                    valid = get_valid_moves(game_state.board, player, opponent)
                    if target in valid:
                        self.reset()
                        return Action(ACTION_MOVE, target)
                    # else: invalid move, just ignore

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.wall_mode:
                cell = cell_from_pixel(*event.pos)
                if cell and cell in self.wall_highlights:
                    self.reset()
                    return Action(ACTION_PLACE_WALL, cell)

        return None
