import pygame
from constants import (
    FRAME_COLOR, FRAME_EDGE, CELL_COLOR, BTN_COLOR, BTN_HOVER,
    TEXT_BROWN, TEXT_CREAM, FONT_HEADING, FONT_BODY
)
from utils import draw_panel, draw_button
from text_input import TextInputBox


class SetupMenu:
    """Intermediate screen to enter player names and choose pieces."""

    def __init__(self, w, h, mode):
        self.w, self.h = w, h
        self.mode = mode
        self.p1_piece = "X"
        self.input1 = TextInputBox("Player 1", placeholder="Player 1 Name", max_len=14)
        self.input2 = TextInputBox("Player 2" if mode != "ai" else "AI", placeholder="Player 2 Name", max_len=14)
        # Select all by default so user can immediately type or tab
        self.input1.active = True
        self.input1.select_all()
        self._layout()

    @property
    def p1_name(self):
        val = self.input1.text.strip()
        return val if val else "Player 1"

    @p1_name.setter
    def p1_name(self, value):
        self.input1.set_text(value)

    @property
    def p2_name(self):
        if self.mode == "ai":
            return "AI"
        val = self.input2.text.strip()
        return val if val else "Player 2"

    @p2_name.setter
    def p2_name(self, value):
        self.input2.set_text(value)

    @property
    def active_box(self):
        if self.input1.active:
            return 1
        elif self.input2.active:
            return 2
        return None

    @active_box.setter
    def active_box(self, val):
        self.input1.active = (val == 1)
        self.input2.active = (val == 2)
        if val == 1:
            self.input1.select_all()
        elif val == 2:
            self.input2.select_all()

    def _layout(self):
        cx = self.w // 2
        pw, ph = 500, 480
        self.panel = pygame.Rect(cx - pw // 2, self.h // 2 - ph // 2, pw, ph)

        base = self.panel.y + 100
        self.box1 = pygame.Rect(cx - 160, base + 40, 320, 45)
        self.input1.set_rect(self.box1)

        # Piece selection buttons
        self.btn_x = pygame.Rect(cx - 80, base + 120, 70, 50)
        self.btn_o = pygame.Rect(cx + 10, base + 120, 70, 50)

        self.box2 = pygame.Rect(cx - 160, base + 210, 320, 45)
        self.input2.set_rect(self.box2)

        # Action buttons
        self.btn_back = pygame.Rect(cx - 180, self.panel.y + ph - 80, 150, 50)
        self.btn_start = pygame.Rect(cx + 30, self.panel.y + ph - 80, 150, 50)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            pos = ev.pos
            res1 = self.input1.handle_mouse_down(pos, FONT_BODY)
            if self.mode != "ai":
                res2 = self.input2.handle_mouse_down(pos, FONT_BODY)
                if res1 == "focus":
                    self.input2.active = False
                    self.input2.clear_selection()
                elif res2 == "focus":
                    self.input1.active = False
                    self.input1.clear_selection()
            else:
                self.input2.active = False

            # Buttons
            if self.btn_x.collidepoint(pos):
                self.p1_piece = "X"
            elif self.btn_o.collidepoint(pos):
                self.p1_piece = "O"
            elif self.btn_back.collidepoint(pos):
                return "back"
            elif self.btn_start.collidepoint(pos):
                return "start"

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.input1.handle_mouse_up()
            if self.mode != "ai":
                self.input2.handle_mouse_up()

        elif ev.type == pygame.MOUSEMOTION:
            self.input1.handle_mouse_motion(ev.pos, FONT_BODY)
            if self.mode != "ai":
                self.input2.handle_mouse_motion(ev.pos, FONT_BODY)

        elif ev.type == pygame.KEYDOWN:
            # Tab cycling
            if ev.key == pygame.K_TAB:
                is_shift = bool(ev.mod & pygame.KMOD_SHIFT)
                if self.mode == "ai":
                    self.input1.active = True
                    self.input1.select_all()
                else:
                    if is_shift:
                        if self.input2.active:
                            self.input2.active = False
                            self.input2.clear_selection()
                            self.input1.active = True
                            self.input1.select_all()
                        else:
                            self.input1.active = False
                            self.input1.clear_selection()
                            self.input2.active = True
                            self.input2.select_all()
                    else:
                        if self.input1.active:
                            self.input1.active = False
                            self.input1.clear_selection()
                            self.input2.active = True
                            self.input2.select_all()
                        else:
                            self.input2.active = False
                            self.input2.clear_selection()
                            self.input1.active = True
                            self.input1.select_all()
                return None

            # Enter to advance / play
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.input1.active and self.mode != "ai":
                    self.input1.active = False
                    self.input1.clear_selection()
                    self.input2.active = True
                    self.input2.select_all()
                    return None
                else:
                    return "start"

            # Key forwarding to active input
            if self.input1.active:
                self.input1.handle_key_down(ev)
            elif self.input2.active and self.mode != "ai":
                self.input2.handle_key_down(ev)

        return None

    def draw(self, screen):
        m = pygame.mouse.get_pos()
        cx = self.w // 2

        # Outer card
        draw_panel(screen, self.panel, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=4)
        inner = pygame.Rect(self.panel.x + 12, self.panel.y + 12, self.panel.width - 24, self.panel.height - 24)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=16, border_w=2, shadow=False)

        # Title
        title_str = "Setup: " + ("Player vs AI" if self.mode == "ai" else "Player vs Player")
        t = FONT_HEADING.render(title_str, True, TEXT_BROWN)
        screen.blit(t, (cx - t.get_width() // 2, self.panel.y + 25))
        pygame.draw.line(screen, FRAME_COLOR, (self.panel.x + 40, self.panel.y + 70), (self.panel.x + self.panel.width - 40, self.panel.y + 70), 2)

        # Player 1 textbox
        p1_lbl = FONT_BODY.render("Player 1 Name:", True, TEXT_BROWN)
        screen.blit(p1_lbl, (self.box1.x, self.box1.y - 30))
        self.input1.draw(screen, FONT_BODY)

        # Piece selection buttons
        piece_lbl = FONT_BODY.render("Choose Piece:", True, TEXT_BROWN)
        screen.blit(piece_lbl, (cx - piece_lbl.get_width() // 2, self.btn_x.y - 35))

        c_x = BTN_HOVER if self.p1_piece == "X" else (FRAME_COLOR if self.btn_x.collidepoint(m) else BTN_COLOR)
        c_o = BTN_HOVER if self.p1_piece == "O" else (FRAME_COLOR if self.btn_o.collidepoint(m) else BTN_COLOR)

        draw_panel(screen, self.btn_x, c_x, FRAME_EDGE, radius=8, border_w=2)
        txt_x = FONT_HEADING.render("X", True, TEXT_CREAM)
        screen.blit(txt_x, (self.btn_x.centerx - txt_x.get_width() // 2, self.btn_x.centery - txt_x.get_height() // 2))

        draw_panel(screen, self.btn_o, c_o, FRAME_EDGE, radius=8, border_w=2)
        txt_o = FONT_HEADING.render("O", True, TEXT_CREAM)
        screen.blit(txt_o, (self.btn_o.centerx - txt_o.get_width() // 2, self.btn_o.centery - txt_o.get_height() // 2))

        # Player 2 textbox or AI label
        if self.mode == "ai":
            p2_lbl = FONT_BODY.render("Opponent: AI", True, TEXT_BROWN)
            screen.blit(p2_lbl, (self.box2.x, self.box2.y - 5))
        else:
            p2_lbl = FONT_BODY.render("Player 2 Name:", True, TEXT_BROWN)
            screen.blit(p2_lbl, (self.box2.x, self.box2.y - 30))
            self.input2.draw(screen, FONT_BODY)

        # Action buttons
        draw_button(screen, self.btn_back, "Back", FONT_BODY, self.btn_back.collidepoint(m))
        draw_button(screen, self.btn_start, "Play!", FONT_BODY, self.btn_start.collidepoint(m))
