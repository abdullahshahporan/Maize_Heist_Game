"""
asset_manager.py — Loads and caches sprite assets from assets/sprites/.
Provides scaled pygame Surfaces for renderer, menu, and screens.
Falls back to None for any missing sprite.
"""

import os
import pygame
from config import ASSET_DIR, CELL_SIZE

SPRITE_DIR = os.path.join(ASSET_DIR, "sprites")

# Mapping: logical name → (filename, target_width, target_height)
# Actual filenames from user's manually-cropped sprites
_SPRITE_DEFS = {
    # ── In-game cell-sized sprites ──────────────────────
    "player1":       ("player1.png",             CELL_SIZE - 4, CELL_SIZE - 4),
    "player2":       ("player2.png",             CELL_SIZE - 4, CELL_SIZE - 4),
    "cash":          ("cash.png",                CELL_SIZE - 10, CELL_SIZE - 10),
    "gold":          ("gold.png",                CELL_SIZE - 10, CELL_SIZE - 10),
    "diamond":       ("diamond.png",             CELL_SIZE - 10, CELL_SIZE - 10),
    "perm_wall":     ("permanent_wall.png",      CELL_SIZE, CELL_SIZE),
    "temp_wall":     ("temp_wall.png",           CELL_SIZE, CELL_SIZE),
    "boundary_wall": ("maze_boundary_wall.png",  CELL_SIZE, CELL_SIZE),

    # ── HUD / small icons ──────────────────────────────
    "timer":         ("timer.png",               24, 32),
    "life_round":    ("life_round.png",          32, 26),
    "cash_value":    ("cash_value.png",          36, 24),
    "gold_value":    ("gold_value.png",          36, 22),
    "diamond_value": ("diamond_value.png",       36, 18),

    # ── Buttons ─────────────────────────────────────────
    "btn_move":       ("move_button.png",        116, 56),
    "btn_place_wall": ("place_wall_button.png",  143, 60),
    "btn_confirm":    ("confirm_button.png",     129, 57),
    "btn_cancel":     ("cancel_button.png",      139, 63),

    # ── Panels ──────────────────────────────────────────
    "turn_info":     ("turn_info.png",           301, 59),

    # ── Title / banners ─────────────────────────────────
    "logo":          ("logo.png",                501, 175),
    "victory":       ("victory_badge.png",       340, 100),
    "game_over":     ("game_over_badge.png",     340, 92),

    # ── Badges ──────────────────────────────────────────
    "badge_win":     ("winner_badge.png",        160, 110),
    "badge_lose":    ("looser_badge.png",        190, 120),
    "badge_draw":    ("draw_badge.png",          166, 102),

    # ── Larger preview versions (menu / end screen) ────
    "player1_big":   ("player1.png",             80, 90),
    "player2_big":   ("player2.png",             86, 88),
    "logo_big":      ("logo.png",                600, 210),
}


class AssetManager:
    """Singleton-ish loader: call init() once after pygame.display is set."""

    def __init__(self):
        self._cache: dict[str, pygame.Surface | None] = {}
        self._loaded = False

    def init(self):
        """Load all sprites (call after pygame.display.set_mode)."""
        if self._loaded:
            return
        self._loaded = True
        for name, (filename, tw, th) in _SPRITE_DEFS.items():
            path = os.path.join(SPRITE_DIR, filename)
            if os.path.isfile(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (tw, th))
                    self._cache[name] = img
                except pygame.error:
                    self._cache[name] = None
            else:
                self._cache[name] = None

    def get(self, name: str) -> pygame.Surface | None:
        return self._cache.get(name)

    @property
    def ready(self) -> bool:
        """True if at least the player sprites loaded."""
        return self._cache.get("player1") is not None


# Module-level singleton
assets = AssetManager()
