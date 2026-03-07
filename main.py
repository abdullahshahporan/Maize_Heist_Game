"""
main.py — Entry point for Maze Heist.
Run this file to start the game:  python main.py
"""

import sys
import os

# Ensure project root is on the path so imports work from any CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE,
    MODE_AI_VS_AI, MODE_AI_VS_HUMAN,
    PLAYER_TYPE_HUMAN, PLAYER_TYPE_MINIMAX, PLAYER_TYPE_ASTAR,
    AI_TIMEOUT,
)
from game.maze_generator import generate_maze
from game.game_state import GameState
from game.actions import ACTION_MOVE, ACTION_PLACE_WALL
from ai.minimax_agent import choose_action_minimax
from ai.astar_agent import choose_action_astar
from ui.renderer import draw_board, draw_end_screen, draw_confirm_exit
from ui.menu import run_main_menu
from ui.screens import draw_opening
from ui.input_handler import HumanInputHandler
from ui.asset_manager import assets
from utils.logger import save_match_log
from utils.helpers import Timer


def build_game_state(mode: str, difficulty: str) -> GameState:
    """Generate maze, assign player types, and return a fresh GameState."""
    board, p1, p2, treasures = generate_maze(difficulty)

    if mode == MODE_AI_VS_AI:
        p1.type = PLAYER_TYPE_MINIMAX
        p1.name = "Minimax AI"
        p2.type = PLAYER_TYPE_ASTAR
        p2.name = "A* Tactical AI"
    else:
        # AI vs Human — human is Player 2, AI is Player 1
        p1.type = PLAYER_TYPE_MINIMAX
        p1.name = "Minimax AI"
        p2.type = PLAYER_TYPE_HUMAN
        p2.name = "Human"

    return GameState(board, p1, p2, treasures, mode, difficulty)


def run_game(screen, clock, game_state: GameState):
    """
    Core game loop.
    Returns:  "menu"  → go back to menu
              "replay" → restart same settings
              "quit"   → exit application
    """
    human_input = HumanInputHandler()
    ai_times = {1: [], 2: []}
    ai_delay_timer = 0              # small visual delay for AI moves
    AI_VISUAL_DELAY = 300           # ms between AI moves for readability
    pending_action = None
    confirming_exit = False

    while True:
        dt = clock.tick(FPS)
        current_player = game_state.get_current_player()

        # ── Event handling ──────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            # Exit confirmation overlay
            if confirming_exit:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        return "menu"
                    elif event.key == pygame.K_n:
                        confirming_exit = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    confirming_exit = True
                    continue

            # Game-over screen input
            if game_state.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "replay"
                    elif event.key == pygame.K_m:
                        return "menu"
                    elif event.key == pygame.K_q:
                        return "quit"
                continue

            # Human turn input
            if current_player.type == PLAYER_TYPE_HUMAN:
                action = human_input.handle_event(event, game_state)
                if action:
                    game_state.apply_action(action)
                    human_input.reset()

        # ── AI turn processing (with visual delay) ─────
        if (not game_state.game_over
                and not confirming_exit
                and current_player.type != PLAYER_TYPE_HUMAN):
            ai_delay_timer += dt
            if ai_delay_timer >= AI_VISUAL_DELAY:
                ai_delay_timer = 0
                with Timer() as t:
                    if current_player.type == PLAYER_TYPE_MINIMAX:
                        action = choose_action_minimax(game_state,
                                                       game_state.difficulty)
                    else:
                        action = choose_action_astar(game_state)
                ai_times[current_player.id].append(t.elapsed)

                if action:
                    game_state.apply_action(action)
                else:
                    # No action → lose
                    game_state.game_over = True
                    game_state.winner = game_state.get_opponent()
                    game_state.end_reason = (
                        f"{current_player.name} returned no action"
                    )

        # ── Drawing ─────────────────────────────────────
        if game_state.game_over:
            game_state.determine_winner()
            draw_end_screen(screen, game_state)
            # Save log once
            if not hasattr(game_state, "_logged"):
                save_match_log(game_state, ai_times)
                game_state._logged = True
        else:
            draw_board(screen, game_state,
                       wall_mode=human_input.wall_mode,
                       wall_highlights=human_input.wall_highlights)

        if confirming_exit:
            draw_confirm_exit(screen)

        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Load sprite assets (must happen after display init)
    assets.init()

    # Opening splash
    if not draw_opening(screen, clock):
        pygame.quit()
        return

    while True:
        # Main menu
        choice = run_main_menu(screen, clock)
        if choice is None:
            break

        mode = choice["mode"]
        difficulty = choice["difficulty"]
        game_state = build_game_state(mode, difficulty)

        while True:
            result = run_game(screen, clock, game_state)
            if result == "quit":
                pygame.quit()
                return
            elif result == "replay":
                game_state = build_game_state(mode, difficulty)
                continue  # play again with same settings
            else:
                break  # "menu" → back to outer loop

    pygame.quit()


if __name__ == "__main__":
    main()
