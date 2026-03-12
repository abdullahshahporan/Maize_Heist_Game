"""
screens.py — Opening splash screen with animated fade-in and particle effects.
"""

import math
import random
import pygame
from config import COLOR_BG, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.asset_manager import assets

_CLR_ACCENT = (255, 200, 50)
_CLR_SUBTITLE = (170, 175, 190)
_CLR_HINT = (120, 125, 140)
_CLR_PANEL = (25, 28, 38)
_CLR_BORDER = (60, 65, 80)

# Floating particle colours (treasure-inspired)
_PARTICLE_COLORS = [
    (100, 200, 100, 120),   # cash green
    (255, 215, 0, 100),     # gold
    (0, 230, 255, 90),      # diamond cyan
    (255, 200, 50, 80),     # accent
]


class _Particle:
    """A small floating particle for visual flair."""
    __slots__ = ("x", "y", "vx", "vy", "size", "color", "life")

    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = random.randint(0, WINDOW_HEIGHT)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.5, -0.1)
        self.size = random.randint(2, 5)
        self.color = random.choice(_PARTICLE_COLORS)
        self.life = random.randint(120, 300)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface, alpha_mult):
        a = min(255, int(self.color[3] * alpha_mult * self.life / 150))
        if a <= 0:
            return
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color[:3], a),
                           (self.size, self.size), self.size)
        surface.blit(s, (int(self.x) - self.size, int(self.y) - self.size))


def draw_opening(screen, clock, duration_ms=4000):
    """Show a polished opening splash screen with particles and animations."""
    start = pygame.time.get_ticks()
    font_big = pygame.font.SysFont("consolas", 52, bold=True)
    font_sm = pygame.font.SysFont("consolas", 15)
    font_hint = pygame.font.SysFont("consolas", 13)
    font_credit = pygame.font.SysFont("consolas", 11)

    logo = assets.get("logo_big")
    p1 = assets.get("player1_big")
    p2 = assets.get("player2_big")

    # Pre-load treasure sprites for the row
    treasure_sprites = []
    for key in ("cash", "gold", "diamond"):
        spr = assets.get(key)
        if spr:
            treasure_sprites.append(pygame.transform.smoothscale(spr, (28, 28)))

    # Particles
    particles = [_Particle() for _ in range(40)]

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
        alpha_f = min(1.0, elapsed / 800.0)
        alpha = int(255 * alpha_f)

        screen.fill(COLOR_BG)
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        # Update and draw particles
        for p in particles:
            p.update()
            p.draw(screen, alpha_f)
        # Replace dead particles
        particles = [p for p in particles if p.life > 0]
        while len(particles) < 30:
            particles.append(_Particle())

        # Central panel backdrop
        panel_w, panel_h = 560, 420
        panel = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2 - 20,
                            panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((*_CLR_PANEL, int(180 * alpha_f)))
        pygame.draw.rect(panel_surf, (*_CLR_BORDER, int(200 * alpha_f)),
                         panel_surf.get_rect(), 2, border_radius=16)
        screen.blit(panel_surf, panel.topleft)

        # Logo / Title
        logo_y = cy - 110
        if logo:
            scaled_logo = pygame.transform.smoothscale(logo, (480, 168))
            lr = scaled_logo.get_rect(center=(cx, logo_y))
            scaled_logo.set_alpha(alpha)
            screen.blit(scaled_logo, lr)
            sub_y = logo_y + 95
        else:
            txt1 = font_big.render("MAZE HEIST", True, _CLR_ACCENT)
            txt1.set_alpha(alpha)
            screen.blit(txt1, txt1.get_rect(center=(cx, logo_y)))
            sub_y = logo_y + 50

        # Subtitle
        txt2 = font_sm.render("A 2D Turn-Based Maze Strategy Game", True, _CLR_SUBTITLE)
        txt2.set_alpha(alpha)
        screen.blit(txt2, txt2.get_rect(center=(cx, sub_y)))

        # Decorative line under subtitle
        line_alpha = int(120 * alpha_f)
        line_surf = pygame.Surface((260, 2), pygame.SRCALPHA)
        line_surf.fill((*_CLR_ACCENT[:3], line_alpha))
        screen.blit(line_surf, (cx - 130, sub_y + 16))

        # Player previews with gentle bob animation
        preview_y = sub_y + 55
        if p1 and p2:
            bob = math.sin(elapsed / 400.0) * 4
            p1.set_alpha(alpha)
            p2.set_alpha(alpha)
            screen.blit(p1, p1.get_rect(center=(cx - 90, preview_y + bob)))
            screen.blit(p2, p2.get_rect(center=(cx + 90, preview_y - bob)))

            # VS badge with glow
            font_vs = pygame.font.SysFont("consolas", 22, bold=True)
            vs = font_vs.render("VS", True, _CLR_ACCENT)
            vs.set_alpha(alpha)
            screen.blit(vs, vs.get_rect(center=(cx, preview_y)))

        # Treasure row below players
        if treasure_sprites:
            t_row_y = preview_y + 60
            total_w = len(treasure_sprites) * 36
            tx = cx - total_w // 2
            for i, tspr in enumerate(treasure_sprites):
                tspr.set_alpha(alpha)
                screen.blit(tspr, (tx + i * 36, t_row_y))

        # Credit
        credit = font_credit.render("KUET  \u00b7  AI Lab  \u00b7  3-2", True, _CLR_HINT)
        credit.set_alpha(alpha)
        screen.blit(credit, credit.get_rect(center=(cx, WINDOW_HEIGHT - 50)))

        # Hint (blink after 1.2s)
        if elapsed > 1200 and (elapsed // 500) % 2 == 0:
            hint = font_hint.render("Press any key to continue...", True, _CLR_HINT)
            screen.blit(hint, hint.get_rect(center=(cx, WINDOW_HEIGHT - 28)))

        pygame.display.flip()
        clock.tick(60)
