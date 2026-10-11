import pygame
from constants import X_DARK, X_LIGHT, O_DARK, O_LIGHT


def draw_x(screen, cx, cy, sz):
    """Draw a carved wooden X piece."""
    t = max(6, sz // 5)
    off = sz
    # Carved shadow
    pygame.draw.line(screen, X_DARK, (cx - off + 2, cy - off + 2), (cx + off + 2, cy + off + 2), t + 3)
    pygame.draw.line(screen, X_DARK, (cx + off + 2, cy - off + 2), (cx - off + 2, cy + off + 2), t + 3)
    # Highlight
    pygame.draw.line(screen, X_LIGHT, (cx - off, cy - off), (cx + off, cy + off), t)
    pygame.draw.line(screen, X_LIGHT, (cx + off, cy - off), (cx - off, cy + off), t)


def draw_o(screen, cx, cy, sz):
    """Draw a carved wooden O piece."""
    t = max(6, sz // 5)
    r = sz + 4
    # Carved shadow
    pygame.draw.circle(screen, O_DARK, (cx + 2, cy + 2), r, t + 3)
    # Highlight
    pygame.draw.circle(screen, O_LIGHT, (cx, cy), r, t)
