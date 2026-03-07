"""
screens.py — Opening splash screen with animated fade-in.
"""

import pygame
from config import COLOR_BG, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.asset_manager import assets

_CLR_ACCENT = (255, 200, 50)
_CLR_SUBTITLE = (170, 175, 190)
_CLR_HINT = (120, 125, 140)


def draw_opening(screen, clock, duration_ms=3000):
    """Show a polished opening splash screen."""
    start = pygame.time.get_ticks()
    font_big = pygame.font.SysFont("consolas", 52, bold=True)
    font_sm = pygame.font.SysFont("consolas", 14)
    font_hint = pygame.font.SysFont("consolas", 13)

    logo = assets.get("logo_big")
    p1 = assets.get("player1_big")
    p2 = assets.get("player2_big")

    while True:
        elapsed = pygame.time.get_ticks() - start
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return True

        if elapsed >= duration_ms:
            return True

        # Fade alpha: 0→255 over the first 800 ms
        alpha = min(255, int(255 * elapsed / 800))

        screen.fill(COLOR_BG)
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        # Logo
        if logo:
            lr = logo.get_rect(center=(cx, cy - 60))
            logo.set_alpha(alpha)
            screen.blit(logo, lr)
            sub_y = cy + 20
        else:
            txt1 = font_big.render("MAZE HEIST", True, _CLR_ACCENT)
            txt1.set_alpha(alpha)
            screen.blit(txt1, txt1.get_rect(center=(cx, cy - 40)))
            sub_y = cy + 20

        # Player previews
        if p1 and p2:
            p1.set_alpha(alpha)
            p2.set_alpha(alpha)
            screen.blit(p1, p1.get_rect(center=(cx - 100, sub_y + 50)))
            screen.blit(p2, p2.get_rect(center=(cx + 100, sub_y + 50)))

            # VS badge
            font_vs = pygame.font.SysFont("consolas", 20, bold=True)
            vs = font_vs.render("VS", True, _CLR_ACCENT)
            vs.set_alpha(alpha)
            screen.blit(vs, vs.get_rect(center=(cx, sub_y + 50)))

        # Subtitle
        txt2 = font_sm.render("A 2D Turn-Based Maze Strategy Game", True, _CLR_SUBTITLE)
        txt2.set_alpha(alpha)
        screen.blit(txt2, txt2.get_rect(center=(cx, sub_y)))

        # Hint (blink after 1s)
        if elapsed > 1000 and (elapsed // 500) % 2 == 0:
            hint = font_hint.render("Press any key to continue...", True, _CLR_HINT)
            screen.blit(hint, hint.get_rect(center=(cx, WINDOW_HEIGHT - 40)))

        pygame.display.flip()
        clock.tick(60)
