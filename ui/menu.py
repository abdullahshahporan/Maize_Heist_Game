"""
menu.py — Start-menu and mode/difficulty selection screens.
Polished sprite-based UI with hover effects.
"""

import pygame
from config import (
    COLOR_BG, COLOR_TEXT, COLOR_BUTTON, COLOR_BUTTON_HOVER,
    COLOR_BUTTON_TEXT, COLOR_TURN_INDICATOR,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    MODE_AI_VS_AI, MODE_AI_VS_HUMAN,
)
from ui.asset_manager import assets

# ── Theme colours ───────────────────────────────────────
_CLR_PANEL = (25, 28, 38)
_CLR_BORDER = (60, 65, 80)
_CLR_ACCENT = (255, 200, 50)
_CLR_BTN = (45, 90, 160)
_CLR_BTN_HOVER = (65, 120, 200)
_CLR_BTN_BORDER = (100, 160, 230)
_CLR_SUBTITLE = (170, 175, 190)


class Button:
    """Styled clickable button with hover glow."""

    def __init__(self, x, y, w, h, text, value=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.value = value
        self.hovered = False

    def draw(self, surface):
        # Shadow
        shadow = self.rect.move(3, 3)
        pygame.draw.rect(surface, (10, 10, 15), shadow, border_radius=10)
        # Body
        clr = _CLR_BTN_HOVER if self.hovered else _CLR_BTN
        pygame.draw.rect(surface, clr, self.rect, border_radius=10)
        # Border
        border_clr = _CLR_ACCENT if self.hovered else _CLR_BTN_BORDER
        pygame.draw.rect(surface, border_clr, self.rect, 2, border_radius=10)
        # Text
        font = pygame.font.SysFont("consolas", 20, bold=True)
        txt = font.render(self.text, True, COLOR_BUTTON_TEXT)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


def run_main_menu(screen, clock) -> dict | None:
    state = "main"
    selected_mode = None

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(COLOR_BG)

        if state == "main":
            buttons = _draw_main(screen, mouse_pos)
        elif state == "mode_select":
            buttons = _draw_mode_select(screen, mouse_pos)
        elif state == "difficulty_select":
            buttons = _draw_difficulty_select(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.clicked(mouse_pos):
                        if state == "main":
                            if b.value == "start":
                                state = "mode_select"
                            elif b.value == "exit":
                                return None
                        elif state == "mode_select":
                            if b.value == "back":
                                state = "main"
                            else:
                                selected_mode = b.value
                                state = "difficulty_select"
                        elif state == "difficulty_select":
                            if b.value == "back":
                                state = "mode_select"
                            else:
                                return {"mode": selected_mode, "difficulty": b.value}
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state in ("mode_select", "difficulty_select"):
                        state = "main"
                    else:
                        return None


# ── Drawing helpers ─────────────────────────────────────

def _draw_main(screen, mouse_pos):
    cx = WINDOW_WIDTH // 2

    # Logo sprite
    logo = assets.get("logo")
    if logo:
        lr = logo.get_rect(center=(cx, 115))
        screen.blit(logo, lr)
        sub_y = 220
    else:
        font_title = pygame.font.SysFont("consolas", 48, bold=True)
        txt = font_title.render("MAZE HEIST", True, _CLR_ACCENT)
        screen.blit(txt, txt.get_rect(center=(cx, 120)))
        sub_y = 180

    # Subtitle
    font_sub = pygame.font.SysFont("consolas", 16)
    txt2 = font_sub.render("A 2D Turn-Based Maze Strategy Game", True, _CLR_SUBTITLE)
    screen.blit(txt2, txt2.get_rect(center=(cx, sub_y)))

    # Player character previews
    p1_spr = assets.get("player1_big")
    p2_spr = assets.get("player2_big")
    preview_y = sub_y + 35
    if p1_spr and p2_spr:
        screen.blit(p1_spr, p1_spr.get_rect(center=(cx - 80, preview_y + 45)))
        screen.blit(p2_spr, p2_spr.get_rect(center=(cx + 80, preview_y + 45)))
        # vs text
        font_vs = pygame.font.SysFont("consolas", 22, bold=True)
        vs_txt = font_vs.render("VS", True, _CLR_ACCENT)
        screen.blit(vs_txt, vs_txt.get_rect(center=(cx, preview_y + 45)))
        btn_y = preview_y + 110
    else:
        btn_y = sub_y + 50

    # Treasure icons row
    for i, key in enumerate(("cash", "gold", "diamond")):
        tspr = assets.get(key)
        if tspr:
            big_t = pygame.transform.smoothscale(tspr, (32, 32))
            screen.blit(big_t, (cx - 52 + i * 36, btn_y))
    btn_y += 45

    bw, bh = 260, 54
    b_start = Button(cx - bw // 2, btn_y, bw, bh, "Start Game", "start")
    b_exit = Button(cx - bw // 2, btn_y + 75, bw, bh, "Exit", "exit")
    buttons = [b_start, b_exit]
    for b in buttons:
        b.update(mouse_pos)
        b.draw(screen)

    # Footer
    font_foot = pygame.font.SysFont("consolas", 11)
    foot = font_foot.render("KUET · AI Lab · 3-2", True, (80, 85, 100))
    screen.blit(foot, foot.get_rect(center=(cx, WINDOW_HEIGHT - 20)))

    return buttons


def _draw_mode_select(screen, mouse_pos):
    cx = WINDOW_WIDTH // 2

    # Header
    _draw_section_header(screen, "Select Game Mode", cx)

    bw, bh = 300, 54
    y = 230
    b1 = Button(cx - bw // 2, y, bw, bh, "AI  vs  AI", MODE_AI_VS_AI)
    b2 = Button(cx - bw // 2, y + 75, bw, bh, "AI  vs  Human", MODE_AI_VS_HUMAN)
    b_back = Button(cx - bw // 2, y + 195, bw, bh, "← Back", "back")
    buttons = [b1, b2, b_back]

    # Player sprites next to buttons
    p1 = assets.get("player1_big")
    p2 = assets.get("player2_big")
    if p1:
        screen.blit(p1, p1.get_rect(center=(cx - bw // 2 - 60, y + 27)))
    if p2:
        screen.blit(p2, p2.get_rect(center=(cx + bw // 2 + 60, y + 27)))

    for b in buttons:
        b.update(mouse_pos)
        b.draw(screen)
    return buttons


def _draw_difficulty_select(screen, mouse_pos):
    cx = WINDOW_WIDTH // 2

    _draw_section_header(screen, "Select Difficulty", cx)

    bw, bh = 260, 54
    y = 220

    diff_labels = [
        ("Easy", "easy", (100, 200, 100)),
        ("Medium", "medium", (255, 200, 50)),
        ("Hard", "hard", (255, 80, 80)),
    ]
    buttons = []
    for i, (label, val, _clr) in enumerate(diff_labels):
        b = Button(cx - bw // 2, y + i * 72, bw, bh, label, val)
        buttons.append(b)

    b_back = Button(cx - bw // 2, y + 3 * 72 + 20, bw, bh, "← Back", "back")
    buttons.append(b_back)

    for b in buttons:
        b.update(mouse_pos)
        b.draw(screen)
    return buttons


def _draw_section_header(screen, text, cx):
    """Draw a styled header with decorative lines."""
    font = pygame.font.SysFont("consolas", 30, bold=True)
    txt = font.render(text, True, _CLR_ACCENT)
    tr = txt.get_rect(center=(cx, 120))
    screen.blit(txt, tr)

    # Decorative lines
    lw = txt.get_width() // 2 + 40
    ly = 148
    pygame.draw.line(screen, _CLR_BORDER, (cx - lw, ly), (cx - 20, ly), 2)
    pygame.draw.line(screen, _CLR_BORDER, (cx + 20, ly), (cx + lw, ly), 2)

    # Logo if available
    logo = assets.get("logo")
    if logo:
        small_logo = pygame.transform.smoothscale(logo, (180, 63))
        screen.blit(small_logo, small_logo.get_rect(center=(cx, 50)))
