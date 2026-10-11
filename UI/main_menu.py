import pygame
from constants import (
    FRAME_COLOR, FRAME_EDGE, CELL_COLOR,
    TEXT_BROWN, FONT_TITLE, FONT_HEADING, FONT_BODY
)
from utils import draw_panel, draw_button


class MainMenu:
    """Clean start screen — pick your game mode."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self._layout()

    def _layout(self):
        bw, bh = 360, 65
        cx = self.w // 2
        pw, ph = 460, 485
        self.panel = pygame.Rect(cx - pw // 2, self.h // 2 - ph // 2, pw, ph)
        base = self.panel.y + 170
        self.btn_ai = pygame.Rect(cx - bw // 2, base, bw, bh)
        self.btn_pvp = pygame.Rect(cx - bw // 2, base + 85, bw, bh)
        self.btn_exit = pygame.Rect(cx - bw // 2, base + 170, bw, bh)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()

    def handle_click(self, pos):
        if self.btn_ai.collidepoint(pos):
            return "ai"
        if self.btn_pvp.collidepoint(pos):
            return "human"
        if self.btn_exit.collidepoint(pos):
            return "exit"
        return None

    def draw(self, screen):
        m = pygame.mouse.get_pos()

        draw_panel(screen, self.panel, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=4)

        inner = pygame.Rect(self.panel.x + 12, self.panel.y + 12,
                            self.panel.width - 24, self.panel.height - 24)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=16, border_w=2, shadow=False)

        t = FONT_TITLE.render("TIC-TAC-TOE", True, TEXT_BROWN)
        screen.blit(t, (self.w // 2 - t.get_width() // 2, self.panel.y + 40))

        ly = self.panel.y + 120
        pygame.draw.line(screen, FRAME_COLOR,
                         (self.panel.x + 50, ly), (self.panel.x + self.panel.width - 50, ly), 2)

        sub = FONT_BODY.render("Select Game Mode", True, TEXT_BROWN)
        screen.blit(sub, (self.w // 2 - sub.get_width() // 2, ly + 12))

        draw_button(screen, self.btn_ai, "Player  vs  AI", FONT_HEADING, self.btn_ai.collidepoint(m))
        draw_button(screen, self.btn_pvp, "Player  vs  Player", FONT_HEADING, self.btn_pvp.collidepoint(m))
        draw_button(screen, self.btn_exit, "Exit Game", FONT_HEADING, self.btn_exit.collidepoint(m))
