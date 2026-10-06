import pygame
import random


def create_bg(w, h):
    """Creates a rich forest-green gradient background with subtle light effects."""
    surf = pygame.Surface((w, h))

    # Smooth vertical gradient
    for y in range(h):
        t = y / h
        r = int(32 + 22 * t)
        g = int(44 + 30 * t)
        b = int(32 + 18 * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    # Subtle bokeh light spots
    for _ in range(15):
        cx = random.randint(0, w)
        cy = random.randint(0, h)
        rad = random.randint(120, 400)
        alpha = random.randint(6, 16)
        blob = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        gv = random.randint(70, 120)
        pygame.draw.circle(blob, (gv, gv + 20, gv - 10, alpha), (rad, rad), rad)
        surf.blit(blob, (cx - rad, cy - rad))

    return surf


def rounded_rect(surface, color, rect, radius=12):
    """Draw a filled rounded rectangle."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_panel(surface, rect, fill, border, radius=14, border_w=3, shadow=True):
    """Professional panel: shadow + fill + border."""
    if shadow:
        s = pygame.Rect(rect.x + 3, rect.y + 3, rect.width, rect.height)
        sh = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 50), sh.get_rect(), border_radius=radius)
        surface.blit(sh, (s.x, s.y))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=border_w, border_radius=radius)


def draw_button(surface, rect, text, font, hovered=False):
    """Wooden-style button with hover feedback."""
    from constants import BTN_COLOR, BTN_HOVER, BTN_TEXT, FRAME_EDGE
    c = BTN_HOVER if hovered else BTN_COLOR
    draw_panel(surface, rect, c, FRAME_EDGE, radius=10, border_w=2, shadow=True)
    t = font.render(text, True, BTN_TEXT)
    surface.blit(t, (rect.centerx - t.get_width() // 2,
                     rect.centery - t.get_height() // 2))
