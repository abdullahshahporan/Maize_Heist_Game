"""
renderer.py — Pygame drawing routines for board, players, treasures, HUD.
Uses sprite assets when available, falls back to primitives.
"""

import pygame
from config import (
    CELL_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    GRID_ROWS, GRID_COLS, WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_BG, COLOR_EMPTY, COLOR_PERM_WALL, COLOR_TEMP_WALL,
    COLOR_PLAYER1, COLOR_PLAYER2,
    COLOR_CASH, COLOR_GOLD, COLOR_DIAMOND,
    COLOR_GRID_LINE, COLOR_TEXT, COLOR_PANEL_BG,
    COLOR_TURN_INDICATOR, COLOR_WALL_MODE, COLOR_HIGHLIGHT,
)
from game.board import CELL_PERM_WALL, CELL_TEMP_WALL
from ui.asset_manager import assets

# ── Constants ───────────────────────────────────────────
TREASURE_COLORS = {"cash": COLOR_CASH, "gold": COLOR_GOLD, "diamond": COLOR_DIAMOND}
_TREASURE_SPRITE = {"cash": "cash", "gold": "gold", "diamond": "diamond"}

# Board area
BOARD_W = GRID_COLS * CELL_SIZE
BOARD_H = GRID_ROWS * CELL_SIZE
BOARD_RIGHT = BOARD_OFFSET_X + BOARD_W
BOARD_BOTTOM = BOARD_OFFSET_Y + BOARD_H

# HUD colours
_CLR_PANEL = (25, 28, 38)
_CLR_PANEL_BORDER = (60, 65, 80)
_CLR_ACCENT = (255, 200, 50)
_CLR_P1 = (80, 170, 255)
_CLR_P2 = (255, 100, 100)
_CLR_GRID_BG = (45, 48, 58)
_CLR_FLOOR = (58, 62, 74)
_CLR_FLOOR_ALT = (52, 56, 68)


def _cell_rect(r, c):
    x = BOARD_OFFSET_X + c * CELL_SIZE
    y = BOARD_OFFSET_Y + r * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def _blit_centered(surface, sprite, rect):
    surface.blit(sprite, sprite.get_rect(center=rect.center))


# ── Top header bar ──────────────────────────────────────
def _draw_header(surface, game_state):
    """Draw a clean header bar with player info and turn/round text."""
    header_h = BOARD_OFFSET_Y - 2
    header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, header_h)
    pygame.draw.rect(surface, _CLR_PANEL, header_rect)
    pygame.draw.line(surface, _CLR_PANEL_BORDER, (0, header_h), (WINDOW_WIDTH, header_h), 2)

    font = pygame.font.SysFont("consolas", 15, bold=True)
    font_sm = pygame.font.SysFont("consolas", 13)
    font_turn = pygame.font.SysFont("consolas", 18, bold=True)
    cp = game_state.get_current_player()
    cx = WINDOW_WIDTH // 2
    mid_y = header_h // 2  # vertical centre of header

    # ── Left: P1 info ───────────────────────────────────
    p1s = assets.get("player1")
    x = 12
    if p1s:
        small_p1 = pygame.transform.smoothscale(p1s, (32, 32))
        surface.blit(small_p1, (x, mid_y - 16))
        x += 38
    p1_name = font.render(game_state.player1.name, True, _CLR_P1)
    surface.blit(p1_name, (x, mid_y - 20))
    p1_score = font.render(f"Score: {game_state.player1.score}", True, COLOR_TEXT)
    surface.blit(p1_score, (x, mid_y + 2))

    # ── Right: P2 info ──────────────────────────────────
    p2s = assets.get("player2")
    p2_name_str = game_state.player2.name
    p2_txt = font.render(p2_name_str, True, _CLR_P2)
    rx = WINDOW_WIDTH - p2_txt.get_width() - 14
    if p2s:
        small_p2 = pygame.transform.smoothscale(p2s, (32, 32))
        surface.blit(small_p2, (rx - 38, mid_y - 16))
    surface.blit(p2_txt, (rx, mid_y - 20))
    p2_score = font.render(f"Score: {game_state.player2.score}", True, COLOR_TEXT)
    surface.blit(p2_score, (rx, mid_y + 2))

    # ── Centre: Turn / Round (clean text only) ──────────
    turn_str = f"Turn {game_state.turn_count}  ·  Round {game_state.round_count}"
    tt = font_turn.render(turn_str, True, _CLR_ACCENT)
    surface.blit(tt, tt.get_rect(center=(cx, mid_y - 10)))

    # Current player indicator
    cp_color = _CLR_P1 if cp.id == 1 else _CLR_P2
    cp_txt = font_sm.render(f"{cp.name}'s Turn", True, cp_color)
    surface.blit(cp_txt, cp_txt.get_rect(center=(cx, mid_y + 14)))


# ── Main board drawing ──────────────────────────────────
def draw_board(surface, game_state, wall_mode=False, wall_highlights=None):
    surface.fill(COLOR_BG)
    board = game_state.board

    pw_spr = assets.get("perm_wall")
    tw_spr = assets.get("temp_wall")
    bw_spr = assets.get("boundary_wall")

    # ── Draw grid cells ─────────────────────────────────
    for r in range(board.rows):
        for c in range(board.cols):
            rect = _cell_rect(r, c)
            cell = board.grid[r][c]
            if cell == CELL_PERM_WALL:
                # Use boundary wall sprite for border cells, perm_wall for interior
                is_border = (r == 0 or r == board.rows - 1 or
                             c == 0 or c == board.cols - 1)
                spr = bw_spr if (is_border and bw_spr) else pw_spr
                if spr:
                    surface.blit(spr, rect.topleft)
                else:
                    pygame.draw.rect(surface, COLOR_PERM_WALL, rect)
            elif cell == CELL_TEMP_WALL:
                if tw_spr:
                    surface.blit(tw_spr, rect.topleft)
                else:
                    pygame.draw.rect(surface, COLOR_TEMP_WALL, rect)
                    _draw_cell_text(surface, "W", rect, 14, (255, 255, 255))
            else:
                # Checkerboard floor
                floor_clr = _CLR_FLOOR if (r + c) % 2 == 0 else _CLR_FLOOR_ALT
                pygame.draw.rect(surface, floor_clr, rect)
            # Grid lines
            pygame.draw.rect(surface, (40, 42, 52), rect, 1)

    # ── Draw treasures ──────────────────────────────────
    for t in game_state.treasures:
        rect = _cell_rect(t.row, t.col)
        spr = assets.get(_TREASURE_SPRITE.get(t.type, "cash"))
        if spr:
            _blit_centered(surface, spr, rect)
        else:
            color = TREASURE_COLORS.get(t.type, COLOR_CASH)
            pygame.draw.circle(surface, color, rect.center, CELL_SIZE // 3)
        # Value badge (bottom-right corner)
        val_spr = assets.get(t.type + "_value")
        if val_spr:
            vr = val_spr.get_rect(bottomright=(rect.right - 1, rect.bottom - 1))
            surface.blit(val_spr, vr)
        else:
            _draw_value_badge(surface, str(t.value), rect)

    # ── Wall placement highlights ───────────────────────
    if wall_mode and wall_highlights:
        hl = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        hl.fill((255, 255, 100, 80))
        pygame.draw.rect(hl, (255, 200, 50, 160), hl.get_rect(), 2)
        for (wr, wc) in wall_highlights:
            surface.blit(hl, _cell_rect(wr, wc).topleft)

    # ── Draw players ────────────────────────────────────
    _draw_player(surface, game_state.player1, COLOR_PLAYER1, "P1", "player1")
    _draw_player(surface, game_state.player2, COLOR_PLAYER2, "P2", "player2")

    # ── Header ──────────────────────────────────────────
    _draw_header(surface, game_state)

    # ── Bottom HUD ──────────────────────────────────────
    _draw_hud(surface, game_state, wall_mode)

    # ── Side panel ──────────────────────────────────────
    _draw_side_panel(surface, game_state)


def _draw_player(surface, player, color, label, sprite_key):
    rect = _cell_rect(player.row, player.col)
    spr = assets.get(sprite_key)
    if spr:
        _blit_centered(surface, spr, rect)
    else:
        center = rect.center
        radius = CELL_SIZE // 2 - 4
        pygame.draw.circle(surface, color, center, radius)
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        _draw_cell_text(surface, label, rect, 14, (255, 255, 255))


def _draw_value_badge(surface, text, rect):
    """Small rounded badge at bottom of cell showing treasure value."""
    font = pygame.font.SysFont("consolas", 11, bold=True)
    txt = font.render(text, True, (255, 255, 255))
    tw, th = txt.get_size()
    bx = rect.centerx - tw // 2 - 3
    by = rect.bottom - th - 4
    bg = pygame.Surface((tw + 6, th + 2), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 170))
    pygame.draw.rect(bg, (0, 0, 0, 170), bg.get_rect(), border_radius=3)
    surface.blit(bg, (bx, by))
    surface.blit(txt, (bx + 3, by + 1))


def _draw_hud(surface, game_state, wall_mode):
    """Bottom info panel with scores and game info."""
    font = pygame.font.SysFont("consolas", 13)
    font_b = pygame.font.SysFont("consolas", 13, bold=True)

    # Panel background
    panel_y = BOARD_BOTTOM + 2
    panel = pygame.Rect(0, panel_y, WINDOW_WIDTH, WINDOW_HEIGHT - panel_y)
    pygame.draw.rect(surface, _CLR_PANEL, panel)
    pygame.draw.line(surface, _CLR_PANEL_BORDER, (0, panel_y), (WINDOW_WIDTH, panel_y), 2)

    px = BOARD_OFFSET_X
    py = panel_y + 6

    # ── Score row ───────────────────────────────────────
    _draw_score_row(surface, px, py, game_state.player1, "P1", _CLR_P1, font, font_b)
    _draw_score_row(surface, px + 310, py, game_state.player2, "P2", _CLR_P2, font, font_b)

    # ── Info row ────────────────────────────────────────
    y2 = py + 20
    mode_label = "AI vs AI" if game_state.game_mode == "ai_vs_ai" else "AI vs Human"
    diff_label = game_state.difficulty.capitalize()
    info_txt = font.render(
        f"Mode: {mode_label}   Difficulty: {diff_label}   "
        f"Temp Walls: {len(game_state.temp_walls)}",
        True, (150, 155, 170),
    )
    surface.blit(info_txt, (px, y2))

    # ── Wall mode indicator ─────────────────────────────
    if wall_mode:
        y3 = y2 + 18
        wm_bg = pygame.Surface((340, 20), pygame.SRCALPHA)
        wm_bg.fill((255, 120, 50, 50))
        surface.blit(wm_bg, (px - 4, y3 - 2))
        wm_txt = font_b.render("⚠ WALL MODE — Click cell or ESC to cancel", True, COLOR_WALL_MODE)
        surface.blit(wm_txt, (px, y3))


def _draw_score_row(surface, x, y, player, label, color, font, font_b):
    """Draw a compact player score with collected count and treasure icons."""
    txt = font_b.render(f"{label}: {player.score}", True, color)
    surface.blit(txt, (x, y))
    sx = x + txt.get_width() + 8
    ct = font.render(f"({player.collected_count} collected)", True, (130, 135, 150))
    surface.blit(ct, (sx, y + 1))
    # Inline treasure icons
    ix = sx + ct.get_width() + 6
    for key in ("cash_value", "gold_value", "diamond_value"):
        icon = assets.get(key)
        if icon:
            surface.blit(icon, (ix, y - 2))
            ix += icon.get_width() + 4


def _draw_side_panel(surface, game_state):
    """Right-side panel showing temp wall info."""
    side_x = BOARD_RIGHT + 10
    side_w = WINDOW_WIDTH - side_x - 6
    side_y = BOARD_OFFSET_Y

    # Panel background
    panel = pygame.Rect(side_x - 6, side_y - 2, side_w + 12, BOARD_H + 4)
    pygame.draw.rect(surface, _CLR_PANEL, panel, border_radius=8)
    pygame.draw.rect(surface, _CLR_PANEL_BORDER, panel, 1, border_radius=8)

    font_h = pygame.font.SysFont("consolas", 13, bold=True)
    font_s = pygame.font.SysFont("consolas", 11)

    ty = side_y + 8

    # Life/round icon
    lr = assets.get("life_round")
    if lr:
        surface.blit(lr, (side_x, ty))
        ty += lr.get_height() + 6

    header = font_h.render("Temp Walls", True, _CLR_ACCENT)
    surface.blit(header, (side_x, ty))
    ty += 20

    pygame.draw.line(surface, _CLR_PANEL_BORDER,
                     (side_x - 2, ty), (side_x + side_w, ty), 1)
    ty += 6

    if not game_state.temp_walls:
        none_txt = font_s.render("None active", True, (100, 105, 120))
        surface.blit(none_txt, (side_x, ty))
    else:
        for tw in game_state.temp_walls[:18]:
            owner_clr = _CLR_P1 if tw.owner_id == 1 else _CLR_P2
            info = f"({tw.row},{tw.col}) R{tw.remaining_rounds}"
            txt = font_s.render(info, True, owner_clr)
            surface.blit(txt, (side_x, ty))
            ty += 14
            if ty > side_y + BOARD_H - 8:
                break


def _draw_cell_text(surface, text, rect, size=16, color=(0, 0, 0)):
    font = pygame.font.SysFont("consolas", size)
    txt = font.render(text, True, color)
    surface.blit(txt, txt.get_rect(center=rect.center))


# ── End screen ──────────────────────────────────────────

def draw_end_screen(surface, game_state):
    surface.fill(COLOR_BG)
    cx = WINDOW_WIDTH // 2
    cy = WINDOW_HEIGHT // 2

    # Determine result
    if game_state.winner:
        is_p1 = game_state.winner.id == 1
        result_text = f"{game_state.winner.name} Wins!"
        result_color = _CLR_P1 if is_p1 else _CLR_P2
        banner = assets.get("victory")
        badge = assets.get("badge_win")
        loser_badge = assets.get("badge_lose")
    else:
        result_text = "It's a Draw!"
        result_color = _CLR_ACCENT
        banner = assets.get("game_over")
        badge = assets.get("badge_draw")
        loser_badge = None

    # Layout
    y = 40

    # Banner
    if banner:
        br = banner.get_rect(center=(cx, y + 50))
        surface.blit(banner, br)
        y += 110
    else:
        font_big = pygame.font.SysFont("consolas", 40, bold=True)
        _blit_center(surface, font_big, result_text, cx, y + 30, result_color)
        y += 70

    # Badge(s)
    if badge:
        if loser_badge and game_state.winner:
            # Winner badge left, loser badge right
            surface.blit(badge, badge.get_rect(center=(cx - 120, y + 60)))
            surface.blit(loser_badge, loser_badge.get_rect(center=(cx + 120, y + 60)))
        else:
            surface.blit(badge, badge.get_rect(center=(cx, y + 55)))
        y += 130
    else:
        y += 20

    font_m = pygame.font.SysFont("consolas", 24, bold=True)
    font_r = pygame.font.SysFont("consolas", 18)
    font_s = pygame.font.SysFont("consolas", 15)

    _blit_center(surface, font_m, result_text, cx, y, result_color)
    y += 35

    _blit_center(surface, font_r, f"Reason: {game_state.end_reason}", cx, y, COLOR_TEXT)
    y += 35

    # Score comparison
    p1s = game_state.player1.score
    p2s = game_state.player2.score
    p1_spr = assets.get("player1_big")
    p2_spr = assets.get("player2_big")

    # Draw player avatars + scores side by side
    score_y = y
    if p1_spr:
        surface.blit(p1_spr, p1_spr.get_rect(center=(cx - 140, score_y + 30)))
    _blit_center(surface, font_m, str(p1s), cx - 140, score_y + 80, _CLR_P1)
    _blit_center(surface, font_s, game_state.player1.name, cx - 140, score_y + 100, (180, 185, 200))

    _blit_center(surface, font_m, "vs", cx, score_y + 80, (120, 125, 140))

    if p2_spr:
        surface.blit(p2_spr, p2_spr.get_rect(center=(cx + 140, score_y + 30)))
    _blit_center(surface, font_m, str(p2s), cx + 140, score_y + 80, _CLR_P2)
    _blit_center(surface, font_s, game_state.player2.name, cx + 140, score_y + 100, (180, 185, 200))

    y = score_y + 130
    _blit_center(surface, font_s,
                 f"Turns: {game_state.turn_count}  |  Rounds: {game_state.round_count}",
                 cx, y, (140, 145, 160))

    # Action buttons
    y += 40
    _blit_center(surface, font_r, "[R] Replay    [M] Menu    [Q] Quit", cx, y, _CLR_ACCENT)


def draw_confirm_exit(surface):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_WIDTH // 2
    cy = WINDOW_HEIGHT // 2

    # Dialog box
    box = pygame.Rect(cx - 200, cy - 80, 400, 160)
    pygame.draw.rect(surface, _CLR_PANEL, box, border_radius=12)
    pygame.draw.rect(surface, _CLR_ACCENT, box, 2, border_radius=12)

    font = pygame.font.SysFont("consolas", 24, bold=True)
    font_sm = pygame.font.SysFont("consolas", 16)
    _blit_center(surface, font, "Leave Game?", cx, cy - 25, COLOR_TEXT)
    _blit_center(surface, font_sm, "[Y] Yes        [N] No", cx, cy + 25, _CLR_ACCENT)


def _blit_center(surface, font, text, cx, y, color):
    txt = font.render(text, True, color)
    surface.blit(txt, txt.get_rect(center=(cx, y)))


def cell_from_pixel(px, py):
    c = (px - BOARD_OFFSET_X) // CELL_SIZE
    r = (py - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
        return (r, c)
    return None
