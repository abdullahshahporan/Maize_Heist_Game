"""
config.py — Central configuration for Maze Heist game.
All constants, colours, sizes, and difficulty settings.
"""

import os

# ── Window ──────────────────────────────────────────────
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 750
FPS = 30
TITLE = "Maze Heist"

# ── Grid ────────────────────────────────────────────────
GRID_ROWS = 12
GRID_COLS = 12
CELL_SIZE = 50
BOARD_OFFSET_X = 20
BOARD_OFFSET_Y = 80

# ── Colours (R, G, B) ──────────────────────────────────
COLOR_BG = (30, 30, 40)
COLOR_EMPTY = (200, 200, 210)
COLOR_PERM_WALL = (50, 50, 60)
COLOR_TEMP_WALL = (160, 100, 50)
COLOR_PLAYER1 = (50, 150, 255)
COLOR_PLAYER2 = (255, 80, 80)
COLOR_CASH = (100, 200, 100)
COLOR_GOLD = (255, 215, 0)
COLOR_DIAMOND = (0, 230, 255)
COLOR_GRID_LINE = (120, 120, 130)
COLOR_HIGHLIGHT = (255, 255, 100, 120)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DARK = (30, 30, 40)
COLOR_PANEL_BG = (40, 40, 55)
COLOR_BUTTON = (70, 130, 200)
COLOR_BUTTON_HOVER = (100, 160, 230)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_TURN_INDICATOR = (255, 200, 50)
COLOR_WALL_MODE = (255, 120, 50)

# ── Treasure Values ────────────────────────────────────
TREASURE_VALUES = {
    "cash": 5,
    "gold": 10,
    "diamond": 20,
}

# ── Treasure Counts (initial) ──────────────────────────
TREASURE_COUNTS = {
    "cash": 6,
    "gold": 4,
    "diamond": 2,
}

# ── Temporary Wall ─────────────────────────────────────
TEMP_WALL_LIFETIME = 5  # full rounds

# ── Turn Limit ─────────────────────────────────────────
MAX_TURNS = 200

# ── Difficulty Settings ────────────────────────────────
DIFFICULTY_SETTINGS = {
    "easy": {
        "minimax_depth": 3,
        "wall_density": 0.10,
        "label": "Easy",
    },
    "medium": {
        "minimax_depth": 5,
        "wall_density": 0.15,
        "label": "Medium",
    },
    "hard": {
        "minimax_depth": 6,
        "wall_density": 0.20,
        "label": "Hard",
    },
}

# ── Game Modes ─────────────────────────────────────────
MODE_AI_VS_AI = "ai_vs_ai"
MODE_AI_VS_HUMAN = "ai_vs_human"

# ── Player Types ───────────────────────────────────────
PLAYER_TYPE_HUMAN = "human"
PLAYER_TYPE_MINIMAX = "minimax"
PLAYER_TYPE_ASTAR = "astar"

# ── Logging ────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# ── Asset dir (optional) ──────────────────────────────
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ── AI Decision Timeout (seconds) ─────────────────────
AI_TIMEOUT = 5.0
