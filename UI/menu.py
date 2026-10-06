import pygame
from constants import *
from utils import draw_panel, draw_button


class MainMenu:
    """Clean start screen — pick your game mode."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self._layout()

    def _layout(self):
        bw, bh = 360, 65
        cx = self.w // 2
        pw, ph = 460, 400
        self.panel = pygame.Rect(cx - pw // 2, self.h // 2 - ph // 2, pw, ph)
        base = self.panel.y + 170
        self.btn_ai = pygame.Rect(cx - bw // 2, base, bw, bh)
        self.btn_pvp = pygame.Rect(cx - bw // 2, base + 85, bw, bh)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()

    def handle_click(self, pos):
        if self.btn_ai.collidepoint(pos):
            return "ai"
        if self.btn_pvp.collidepoint(pos):
            return "human"
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


class SetupMenu:
    """Intermediate screen to enter names and choose pieces."""
    def __init__(self, w, h, mode):
        self.w, self.h = w, h
        self.mode = mode
        self.p1_name = "Player 1"
        self.p2_name = "AI" if mode == "ai" else "Player 2"
        self.p1_piece = "X"
        self.active_box = None
        self._layout()

    def _layout(self):
        cx = self.w // 2
        pw, ph = 500, 480
        self.panel = pygame.Rect(cx - pw//2, self.h//2 - ph//2, pw, ph)

        base = self.panel.y + 100
        self.box1 = pygame.Rect(cx - 160, base + 40, 320, 45)
        
        # Piece selection buttons
        self.btn_x = pygame.Rect(cx - 80, base + 120, 70, 50)
        self.btn_o = pygame.Rect(cx + 10, base + 120, 70, 50)

        self.box2 = pygame.Rect(cx - 160, base + 210, 320, 45)

        # Action buttons
        self.btn_back = pygame.Rect(cx - 180, self.panel.y + ph - 80, 150, 50)
        self.btn_start = pygame.Rect(cx + 30, self.panel.y + ph - 80, 150, 50)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()
        
    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            pos = ev.pos
            # Text box focus
            if self.box1.collidepoint(pos): self.active_box = 1
            elif self.box2.collidepoint(pos) and self.mode != "ai": self.active_box = 2
            else: self.active_box = None
            
            # Button clicks
            if self.btn_x.collidepoint(pos): self.p1_piece = "X"
            elif self.btn_o.collidepoint(pos): self.p1_piece = "O"
            elif self.btn_back.collidepoint(pos): return "back"
            elif self.btn_start.collidepoint(pos): return "start"

        elif ev.type == pygame.KEYDOWN and self.active_box:
            if ev.key == pygame.K_BACKSPACE:
                if self.active_box == 1: self.p1_name = self.p1_name[:-1]
                else: self.p2_name = self.p2_name[:-1]
            else:
                char = ev.unicode
                if char.isprintable() and len(char) > 0:
                    if self.active_box == 1 and len(self.p1_name) < 12: self.p1_name += char
                    elif self.active_box == 2 and len(self.p2_name) < 12: self.p2_name += char
        return None
        
    def _draw_textbox(self, screen, rect, text, active):
        bc = FRAME_COLOR if active else FRAME_EDGE
        draw_panel(screen, rect, CELL_COLOR, bc, radius=6, border_w=3 if active else 2, shadow=False)
        txt = FONT_BODY.render(text + ("|" if active else ""), True, TEXT_BROWN)
        screen.blit(txt, (rect.x + 10, rect.centery - txt.get_height()//2))

    def draw(self, screen):
        m = pygame.mouse.get_pos()
        cx = self.w // 2

        # Main Panel
        draw_panel(screen, self.panel, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=4)
        inner = pygame.Rect(self.panel.x + 12, self.panel.y + 12, self.panel.width - 24, self.panel.height - 24)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=16, border_w=2, shadow=False)

        # Title
        title_str = "Setup: " + ("Player vs AI" if self.mode == "ai" else "Player vs Player")
        t = FONT_HEADING.render(title_str, True, TEXT_BROWN)
        screen.blit(t, (cx - t.get_width()//2, self.panel.y + 25))
        pygame.draw.line(screen, FRAME_COLOR, (self.panel.x + 40, self.panel.y + 70), (self.panel.x + self.panel.width - 40, self.panel.y + 70), 2)

        # Player 1
        p1_lbl = FONT_BODY.render("Player 1 Name:", True, TEXT_BROWN)
        screen.blit(p1_lbl, (self.box1.x, self.box1.y - 30))
        self._draw_textbox(screen, self.box1, self.p1_name, self.active_box == 1)

        # Piece selection
        piece_lbl = FONT_BODY.render("Choose Piece:", True, TEXT_BROWN)
        screen.blit(piece_lbl, (cx - piece_lbl.get_width()//2, self.btn_x.y - 35))
        
        c_x = BTN_HOVER if self.p1_piece == "X" else (FRAME_COLOR if self.btn_x.collidepoint(m) else BTN_COLOR)
        c_o = BTN_HOVER if self.p1_piece == "O" else (FRAME_COLOR if self.btn_o.collidepoint(m) else BTN_COLOR)
        
        draw_panel(screen, self.btn_x, c_x, FRAME_EDGE, radius=8, border_w=2)
        txt_x = FONT_HEADING.render("X", True, TEXT_CREAM)
        screen.blit(txt_x, (self.btn_x.centerx - txt_x.get_width()//2, self.btn_x.centery - txt_x.get_height()//2))

        draw_panel(screen, self.btn_o, c_o, FRAME_EDGE, radius=8, border_w=2)
        txt_o = FONT_HEADING.render("O", True, TEXT_CREAM)
        screen.blit(txt_o, (self.btn_o.centerx - txt_o.get_width()//2, self.btn_o.centery - txt_o.get_height()//2))

        # Player 2
        if self.mode == "ai":
            p2_lbl = FONT_BODY.render("Opponent: AI", True, TEXT_BROWN)
            screen.blit(p2_lbl, (self.box2.x, self.box2.y - 5))
        else:
            p2_lbl = FONT_BODY.render("Player 2 Name:", True, TEXT_BROWN)
            screen.blit(p2_lbl, (self.box2.x, self.box2.y - 30))
            self._draw_textbox(screen, self.box2, self.p2_name, self.active_box == 2)

        # Buttons
        draw_button(screen, self.btn_back, "Back", FONT_BODY, self.btn_back.collidepoint(m))
        draw_button(screen, self.btn_start, "Play!", FONT_BODY, self.btn_start.collidepoint(m))
