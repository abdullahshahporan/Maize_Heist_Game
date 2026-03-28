"""
renderer.py — Pygame drawing routines for board, players, treasures, HUD.
Uses sprite assets when available, falls back to primitives.
Enhanced with last-move indicators, speed display, and polished visuals.
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
    TREASURE_VALUES, MODE_AI_VS_HUMAN,
)
from game.board import CELL_PERM_WALL, CELL_TEMP_WALL
from game.actions import ACTION_MOVE, ACTION_PLACE_WALL
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


def _draw_keycap(surface, text, x, y, w=24, h=20):
    """Draw a styled keyboard key cap."""
    pygame.draw.rect(surface, (12, 14, 20),
                     pygame.Rect(x + 1, y + 2, w, h), border_radius=4)
    key = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (50, 55, 70), key, border_radius=4)
    pygame.draw.rect(surface, (85, 90, 105), key, 1, border_radius=4)
    fsize = 10 if len(text) > 2 else (11 if len(text) > 1 else 12)
    font = pygame.font.SysFont("consolas", fsize, bold=True)
    txt = font.render(text, True, (215, 220, 230))
    surface.blit(txt, txt.get_rect(center=key.center))


def _draw_panel_section(surface, title, x, y, w):
    """Draw a section header with accent-colored title and divider."""
    font = pygame.font.SysFont("consolas", 12, bold=True)
    txt = font.render(title, True, _CLR_ACCENT)
    surface.blit(txt, (x, y))
    line_y = y + 16
    pygame.draw.line(surface, _CLR_PANEL_BORDER,
                     (x - 2, line_y), (x + w, line_y), 1)
    return line_y + 5


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
    p1_score_str = f"Score: {game_state.player1.score}"
    p1_score = font.render(p1_score_str, True, COLOR_TEXT)
    surface.blit(p1_score, (x, mid_y + 2))

    # ── Right: P2 info (right-align based on widest text) ──
    p2s = assets.get("player2")
    p2_name_str = game_state.player2.name
    p2_score_str = f"Score: {game_state.player2.score}"
    p2_name_surf = font.render(p2_name_str, True, _CLR_P2)
    p2_score_surf = font.render(p2_score_str, True, COLOR_TEXT)
    max_w = max(p2_name_surf.get_width(), p2_score_surf.get_width())
    rx = WINDOW_WIDTH - max_w - 14
    if p2s:
        small_p2 = pygame.transform.smoothscale(p2s, (32, 32))
        surface.blit(small_p2, (rx - 38, mid_y - 16))
    surface.blit(p2_name_surf, (rx, mid_y - 20))
    surface.blit(p2_score_surf, (rx, mid_y + 2))

    # ── Centre: Turn / Round (clean text only) ──────────
    turn_str = f"Turn {game_state.turn_count}  ·  Round {game_state.round_count}"
    tt = font_turn.render(turn_str, True, _CLR_ACCENT)
    surface.blit(tt, tt.get_rect(center=(cx, mid_y - 10)))

    # Current player indicator
    cp_color = _CLR_P1 if cp.id == 1 else _CLR_P2
    cp_txt = font_sm.render(f"{cp.name}'s Turn", True, cp_color)
    surface.blit(cp_txt, cp_txt.get_rect(center=(cx, mid_y + 14)))

    # Vertical separators
    pygame.draw.line(surface, _CLR_PANEL_BORDER,
                     (cx - 100, 10), (cx - 100, header_h - 10), 1)
    pygame.draw.line(surface, _CLR_PANEL_BORDER,
                     (cx + 100, 10), (cx + 100, header_h - 10), 1)


# ── Main board drawing ──────────────────────────────────
def draw_board(surface, game_state, wall_mode=False, wall_highlights=None):
    surface.fill(COLOR_BG)
    board = game_state.board

    pw_spr = assets.get("perm_wall")
    tw_spr = assets.get("temp_wall")
    bw_spr = assets.get("boundary_wall")
    # Build a lookup: (row, col) -> owner_id for temp walls so we can label them
    _tw_owners = {(w.row, w.col): w.owner_id
                  for w in getattr(game_state, 'temp_walls', [])}
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
                _tw_owner = _tw_owners.get((r, c), 0)
                _tw_label = "M" if _tw_owner == 1 else "A"
                # Owner tint: blue for Minimax (P1), red for A* (P2)
                _tw_tint = (80, 130, 220) if _tw_owner == 1 else (220, 80, 80)
                if tw_spr:
                    surface.blit(tw_spr, rect.topleft)
                else:
                    pygame.draw.rect(surface, COLOR_TEMP_WALL, rect)
                # Draw a small coloured badge in the top-left corner
                badge = pygame.Rect(rect.x + 2, rect.y + 2, 16, 16)
                pygame.draw.rect(surface, _tw_tint, badge, border_radius=3)
                pygame.draw.rect(surface, (255, 255, 255), badge, 1, border_radius=3)
                _lbl_font = pygame.font.SysFont("consolas", 11, bold=True)
                _lbl_surf = _lbl_font.render(_tw_label, True, (255, 255, 255))
                surface.blit(_lbl_surf, _lbl_surf.get_rect(center=badge.center))
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

    # ── Last move indicator ─────────────────────────────
    last_action = getattr(game_state, 'last_action', None)
    last_pid = getattr(game_state, 'last_action_player_id', None)
    if last_action and last_pid:
        lr, lc = last_action.target
        last_rect = _cell_rect(lr, lc)
        if last_action.action_type == ACTION_MOVE:
            # Pulsing green border for move
            clr = (100, 255, 100, 140) if last_pid == 1 else (255, 120, 120, 140)
            indicator = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(indicator, clr, indicator.get_rect(), 3, border_radius=4)
            surface.blit(indicator, last_rect.topleft)
        elif last_action.action_type == ACTION_PLACE_WALL:
            # Orange border for wall placement
            indicator = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(indicator, (255, 160, 50, 180), indicator.get_rect(), 3, border_radius=4)
            surface.blit(indicator, last_rect.topleft)

    # ── Draw players ────────────────────────────────────
    cp = game_state.get_current_player()
    _draw_player(surface, game_state.player1, COLOR_PLAYER1, "P1", "player1",
                 is_active=(cp.id == 1))
    _draw_player(surface, game_state.player2, COLOR_PLAYER2, "P2", "player2",
                 is_active=(cp.id == 2))

    # ── Header ──────────────────────────────────────────
    _draw_header(surface, game_state)

    # ── Bottom HUD ──────────────────────────────────────
    _draw_hud(surface, game_state, wall_mode)

    # ── Board frame ───────────────────────────────────
    frame = pygame.Rect(BOARD_OFFSET_X - 3, BOARD_OFFSET_Y - 3,
                        BOARD_W + 6, BOARD_H + 6)
    pygame.draw.rect(surface, _CLR_PANEL_BORDER, frame, 2, border_radius=2)

    # ── Side panel ────────────────────────────────────
    _draw_side_panel(surface, game_state, wall_mode)


def _draw_player(surface, player, color, label, sprite_key, is_active=False):
    rect = _cell_rect(player.row, player.col)
    # Active player glow ring
    if is_active:
        glow = pygame.Surface((CELL_SIZE + 8, CELL_SIZE + 8), pygame.SRCALPHA)
        glow_clr = (*color[:3], 60)
        pygame.draw.circle(glow, glow_clr,
                           (CELL_SIZE // 2 + 4, CELL_SIZE // 2 + 4),
                           CELL_SIZE // 2 + 2)
        surface.blit(glow, (rect.x - 4, rect.y - 4))
    spr = assets.get(sprite_key)
    if spr:
        _blit_centered(surface, spr, rect)
    else:
        center = rect.center
        radius = CELL_SIZE // 2 - 4
        pygame.draw.circle(surface, color, center, radius)
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        _draw_cell_text(surface, label, rect, 14, (255, 255, 255))
    # Active border
    if is_active:
        pygame.draw.rect(surface, _CLR_ACCENT, rect, 2, border_radius=3)


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
    font_b = pygame.font.SysFont("consolas", 14, bold=True)
    font_sm = pygame.font.SysFont("consolas", 11)

    # Panel background
    panel_y = BOARD_BOTTOM + 2
    panel = pygame.Rect(0, panel_y, WINDOW_WIDTH, WINDOW_HEIGHT - panel_y)
    pygame.draw.rect(surface, _CLR_PANEL, panel)
    pygame.draw.line(surface, _CLR_PANEL_BORDER, (0, panel_y), (WINDOW_WIDTH, panel_y), 2)

    px = BOARD_OFFSET_X
    py = panel_y + 6

    # ── Score bars ──────────────────────────────────────
    total = game_state.player1.score + game_state.player2.score
    bar_w = 280
    bar_h = 14

    # P1 score bar
    p1_spr = assets.get("player1")
    sx = px
    if p1_spr:
        tiny = pygame.transform.smoothscale(p1_spr, (18, 18))
        surface.blit(tiny, (sx, py))
        sx += 22
    p1_label = font_b.render(f"{game_state.player1.name}: {game_state.player1.score}",
                             True, _CLR_P1)
    surface.blit(p1_label, (sx, py))

    # P2 score bar
    p2_x = px + 340
    p2_spr = assets.get("player2")
    sx2 = p2_x
    if p2_spr:
        tiny2 = pygame.transform.smoothscale(p2_spr, (18, 18))
        surface.blit(tiny2, (sx2, py))
        sx2 += 22
    p2_label = font_b.render(f"{game_state.player2.name}: {game_state.player2.score}",
                             True, _CLR_P2)
    surface.blit(p2_label, (sx2, py))

    # Score comparison bar
    bar_y = py + 22
    bar_total_w = BOARD_W
    pygame.draw.rect(surface, (40, 43, 55),
                     pygame.Rect(px, bar_y, bar_total_w, bar_h), border_radius=4)
    if total > 0:
        p1_w = int(bar_total_w * game_state.player1.score / total)
        if p1_w > 0:
            pygame.draw.rect(surface, _CLR_P1,
                             pygame.Rect(px, bar_y, p1_w, bar_h),
                             border_radius=4)
        p2_w = bar_total_w - p1_w
        if p2_w > 0:
            pygame.draw.rect(surface, _CLR_P2,
                             pygame.Rect(px + p1_w, bar_y, p2_w, bar_h),
                             border_radius=4)
    else:
        # No score yet — half/half placeholder
        mid = bar_total_w // 2
        pygame.draw.rect(surface, (55, 60, 75),
                         pygame.Rect(px, bar_y, mid, bar_h), border_radius=4)

    # ── Info row below bar ──────────────────────────────
    y2 = bar_y + bar_h + 4
    remaining = len(game_state.treasures)
    info_txt = font_sm.render(
        f"Treasures: {remaining}   |   Walls: {len(game_state.temp_walls)}   |   "
        f"Round: {game_state.round_count}   |   Turn: {game_state.turn_count}",
        True, (130, 135, 150),
    )
    surface.blit(info_txt, (px, y2))

    # ── Wall mode indicator ─────────────────────────────
    if wall_mode:
        wm_y = y2 + 16
        wm_bg = pygame.Surface((340, 18), pygame.SRCALPHA)
        wm_bg.fill((255, 120, 50, 50))
        surface.blit(wm_bg, (px - 4, wm_y - 1))
        wm_txt = font_b.render("WALL MODE — Click cell or press ESC", True, COLOR_WALL_MODE)
        surface.blit(wm_txt, (px, wm_y))


def _draw_side_panel(surface, game_state, wall_mode=False):
    """Right-side panel: scores, game info, controls, treasure legend, temp walls."""
    side_x = BOARD_RIGHT + 14
    side_w = WINDOW_WIDTH - BOARD_RIGHT - 22
    side_y = BOARD_OFFSET_Y
    panel_h = BOARD_H + 8

    # Panel background
    panel_rect = pygame.Rect(BOARD_RIGHT + 5, side_y - 4,
                             WINDOW_WIDTH - BOARD_RIGHT - 10, panel_h)
    pygame.draw.rect(surface, _CLR_PANEL, panel_rect, border_radius=10)
    pygame.draw.rect(surface, _CLR_PANEL_BORDER, panel_rect, 1, border_radius=10)

    font_s = pygame.font.SysFont("consolas", 11)
    font_val = pygame.font.SysFont("consolas", 11, bold=True)
    font_score = pygame.font.SysFont("consolas", 16, bold=True)
    font_score_sm = pygame.font.SysFont("consolas", 11)

    ty = side_y + 8

    # ── Section: Scores (prominent) ───────────────────────
    ty = _draw_panel_section(surface, "SCORES", side_x, ty, side_w)

    cp = game_state.get_current_player()
    for player, clr, label in [
        (game_state.player1, _CLR_P1, "P1"),
        (game_state.player2, _CLR_P2, "P2"),
    ]:
        # Player icon
        spr = assets.get("player1" if player.id == 1 else "player2")
        ix = side_x
        if spr:
            small = pygame.transform.smoothscale(spr, (20, 20))
            surface.blit(small, (ix, ty + 1))
            ix += 24

        # Name
        nt = font_val.render(player.name, True, clr)
        surface.blit(nt, (ix, ty + 3))

        # Score value (right-aligned)
        st = font_score.render(str(player.score), True, clr)
        surface.blit(st, (side_x + side_w - st.get_width(), ty))

        # Active turn indicator
        if player.id == cp.id:
            dot_x = side_x + side_w - st.get_width() - 10
            pygame.draw.circle(surface, _CLR_ACCENT, (dot_x, ty + 10), 3)

        ty += 22

        # Collected count
        ct = font_s.render(f"{player.collected_count} collected", True, (110, 115, 130))
        surface.blit(ct, (ix, ty))
        ty += 16

    ty += 4

    # ── Section: Game Info ────────────────────────────────
    ty = _draw_panel_section(surface, "GAME INFO", side_x, ty, side_w)

    mode_label = "AI vs Human" if game_state.game_mode == MODE_AI_VS_HUMAN else "AI vs AI"
    diff_label = game_state.difficulty.capitalize()
    info_pairs = [
        ("Mode:", mode_label),
        ("Difficulty:", diff_label),
        ("Round:", str(game_state.round_count)),
        ("Turn:", str(game_state.turn_count)),
    ]
    for lab, val in info_pairs:
        lt = font_s.render(lab, True, (140, 145, 160))
        surface.blit(lt, (side_x, ty))
        vt = font_val.render(val, True, COLOR_TEXT)
        surface.blit(vt, (side_x + 78, ty))
        ty += 15
    ty += 4

    # ── Section: Controls (Human mode only) ───────────────
    is_human = game_state.game_mode == MODE_AI_VS_HUMAN
    if is_human:
        ty = _draw_panel_section(surface, "CONTROLS", side_x, ty, side_w)

        # Movement sub-section with button sprite
        btn_mv = assets.get("btn_move")
        if btn_mv:
            scaled = pygame.transform.smoothscale(btn_mv, (68, 32))
            surface.blit(scaled, (side_x, ty))
            ty += 34
        else:
            mvh = font_val.render("Movement", True, (180, 185, 200))
            surface.blit(mvh, (side_x, ty))
            ty += 16

        # WASD keys in diamond layout
        kx = side_x
        _draw_keycap(surface, "W", kx + 26, ty, 22, 18)
        ty += 21
        _draw_keycap(surface, "A", kx, ty, 22, 18)
        _draw_keycap(surface, "S", kx + 26, ty, 22, 18)
        _draw_keycap(surface, "D", kx + 52, ty, 22, 18)
        desc = font_s.render("Move (Arrows too)", True, (150, 155, 170))
        surface.blit(desc, (kx + 80, ty + 2))
        ty += 24

        # Wall placement sub-section with button sprite
        btn_pw = assets.get("btn_place_wall")
        if btn_pw:
            scaled = pygame.transform.smoothscale(btn_pw, (80, 34))
            surface.blit(scaled, (side_x, ty))
            ty += 36
        else:
            pwh = font_val.render("Wall Placement", True, (180, 185, 200))
            surface.blit(pwh, (side_x, ty))
            ty += 16

        # Quick wall keys in diamond layout
        kx = side_x
        _draw_keycap(surface, "T", kx + 26, ty, 22, 18)
        ty += 21
        _draw_keycap(surface, "L", kx, ty, 22, 18)
        _draw_keycap(surface, "B", kx + 26, ty, 22, 18)
        _draw_keycap(surface, "R", kx + 52, ty, 22, 18)
        wd = font_s.render("Place Wall", True, (150, 155, 170))
        surface.blit(wd, (kx + 80, ty + 2))
        ty += 24

        _draw_keycap(surface, "E", side_x, ty, 22, 18)
        et = font_s.render("Wall Mode + Click", True, (150, 155, 170))
        surface.blit(et, (side_x + 28, ty + 2))
        ty += 22

        _draw_keycap(surface, "ESC", side_x, ty, 34, 18)
        esc_t = font_s.render("Cancel", True, (150, 155, 170))
        surface.blit(esc_t, (side_x + 40, ty + 2))
        ty += 24

        # Wall mode active indicator
        if wall_mode:
            wm_surf = pygame.Surface((side_w + 4, 18), pygame.SRCALPHA)
            wm_surf.fill((255, 120, 50, 45))
            surface.blit(wm_surf, (side_x - 4, ty))
            wm_border = pygame.Rect(side_x - 4, ty, side_w + 4, 18)
            pygame.draw.rect(surface, (255, 140, 60), wm_border, 1, border_radius=3)
            wm_font = pygame.font.SysFont("consolas", 10, bold=True)
            wm_txt = wm_font.render("WALL MODE ACTIVE", True, (255, 160, 80))
            surface.blit(wm_txt, (side_x, ty + 3))
            ty += 22
        ty += 2

    # ── Section: Treasure Values ──────────────────────────
    ty = _draw_panel_section(surface, "TREASURES", side_x, ty, side_w)

    treasure_info = [
        ("cash", "Cash", TREASURE_VALUES["cash"], COLOR_CASH),
        ("gold", "Gold", TREASURE_VALUES["gold"], COLOR_GOLD),
        ("diamond", "Diamond", TREASURE_VALUES["diamond"], COLOR_DIAMOND),
    ]
    for sprite_key, name, value, color in treasure_info:
        spr = assets.get(sprite_key)
        if spr:
            small = pygame.transform.smoothscale(spr, (16, 16))
            surface.blit(small, (side_x, ty + 1))
        else:
            pygame.draw.circle(surface, color, (side_x + 8, ty + 9), 6)
        nt = font_s.render(name, True, (180, 185, 200))
        surface.blit(nt, (side_x + 22, ty + 2))
        vt = font_val.render(f"= {value} pts", True, color)
        surface.blit(vt, (side_x + 90, ty + 2))
        ty += 20

    remaining = len(game_state.treasures)
    rem_txt = font_s.render(f"Remaining: {remaining}", True, (140, 145, 160))
    surface.blit(rem_txt, (side_x, ty + 1))
    ty += 18

    # ── Section: Temp Walls ───────────────────────────────
    ty = _draw_panel_section(surface, "TEMP WALLS", side_x, ty, side_w)

    if not game_state.temp_walls:
        none_t = font_s.render("None active", True, (100, 105, 120))
        surface.blit(none_t, (side_x, ty))
    else:
        for tw in game_state.temp_walls[:6]:
            owner_clr = _CLR_P1 if tw.owner_id == 1 else _CLR_P2
            info = f"({tw.row},{tw.col})  {tw.remaining_rounds} rnd"
            txt = font_s.render(info, True, owner_clr)
            surface.blit(txt, (side_x, ty))
            ty += 14
            if ty > side_y + panel_h - 16:
                break

    # ── Section: Last Action ──────────────────────────────
    ty += 4
    if ty < side_y + panel_h - 60:
        ty = _draw_panel_section(surface, "LAST ACTION", side_x, ty, side_w)
        last_action = getattr(game_state, 'last_action', None)
        last_pid = getattr(game_state, 'last_action_player_id', None)
        if last_action and last_pid:
            pname = game_state.player1.name if last_pid == 1 else game_state.player2.name
            pclr = _CLR_P1 if last_pid == 1 else _CLR_P2
            act_type = "Move" if last_action.action_type == ACTION_MOVE else "Wall"
            r, c = last_action.target
            at = font_val.render(f"{pname}", True, pclr)
            surface.blit(at, (side_x, ty))
            ty += 14
            dt = font_s.render(f"{act_type} → ({r},{c})", True, (170, 175, 190))
            surface.blit(dt, (side_x, ty))
            ty += 14
        else:
            nt = font_s.render("None yet", True, (100, 105, 120))
            surface.blit(nt, (side_x, ty))
            ty += 14


def _draw_cell_text(surface, text, rect, size=16, color=(0, 0, 0)):
    font = pygame.font.SysFont("consolas", size)
    txt = font.render(text, True, color)
    surface.blit(txt, txt.get_rect(center=rect.center))


# ── End screen ──────────────────────────────────────────

def draw_end_screen(surface, game_state):
    surface.fill(COLOR_BG)
    cx = WINDOW_WIDTH // 2
    cy = WINDOW_HEIGHT // 2

    # Central panel background
    panel_w, panel_h = 680, 600
    panel = pygame.Rect(cx - panel_w // 2, 25, panel_w, panel_h)
    pygame.draw.rect(surface, _CLR_PANEL, panel, border_radius=16)
    pygame.draw.rect(surface, _CLR_PANEL_BORDER, panel, 2, border_radius=16)

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

    # Detailed stats
    y += 24
    p1_col = game_state.player1.collected_count
    p2_col = game_state.player2.collected_count
    p1_walls = game_state.wall_placements.get(1, 0)
    p2_walls = game_state.wall_placements.get(2, 0)
    stats_font = pygame.font.SysFont("consolas", 13)
    _blit_center(surface, stats_font,
                 f"Collected: {p1_col} vs {p2_col}  |  Walls placed: {p1_walls} vs {p2_walls}",
                 cx, y, (120, 125, 140))

    # Action hints with keycaps
    y += 40
    font_act = pygame.font.SysFont("consolas", 14)
    actions = [("R", "Replay"), ("M", "Menu"), ("Q", "Quit")]
    ax = cx - 140
    for key, label in actions:
        _draw_keycap(surface, key, ax, y - 10, 28, 22)
        lt = font_act.render(label, True, (180, 185, 200))
        surface.blit(lt, (ax + 34, y - 4))
        ax += 100


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

    _draw_keycap(surface, "Y", cx - 60, cy + 14, 28, 22)
    yt = font_sm.render("Yes", True, _CLR_ACCENT)
    surface.blit(yt, (cx - 28, cy + 18))
    _draw_keycap(surface, "N", cx + 30, cy + 14, 28, 22)
    nt = font_sm.render("No", True, _CLR_ACCENT)
    surface.blit(nt, (cx + 62, cy + 18))


def _blit_center(surface, font, text, cx, y, color):
    txt = font.render(text, True, color)
    surface.blit(txt, txt.get_rect(center=(cx, y)))


def cell_from_pixel(px, py):
    c = (px - BOARD_OFFSET_X) // CELL_SIZE
    r = (py - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
        return (r, c)
    return None
