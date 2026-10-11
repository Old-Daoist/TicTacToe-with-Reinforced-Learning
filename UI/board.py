import pygame
from constants import (
    TITLEBAR_H, FRAME_COLOR, FRAME_EDGE, CELL_COLOR, CELL_HOVER, CELL_WIN,
    TEXT_BROWN, TEXT_CREAM, GOLD, GOLD_LIGHT, FONT_HEADING, FONT_BODY,
    get_board_layout
)
from utils import draw_panel, draw_button
from pieces import draw_x, draw_o
from popup import VictoryPopup
from ai_agent import AIAgent


class GameBoard:
    """The main game screen:
       Toolbar -> Status pill -> Centered board -> Score footer
       History drawer overlays from the right."""

    def __init__(self, w, h, mode, p1_name, p2_name, p1_piece, history):
        self.w, self.h = w, h
        self.mode = mode
        self.history = history
        self.p1_name = p1_name.strip() if p1_name.strip() else "Player 1"
        self.p2_name = p2_name.strip() if p2_name.strip() else ("AI" if mode == "ai" else "Player 2")
        self.p1_piece = p1_piece

        # Determine roles based on P1's piece selection
        if p1_piece == "X":
            self.x_name = self.p1_name
            self.o_name = self.p2_name
            self.ai_piece = 2
        else:
            self.x_name = self.p2_name
            self.o_name = self.p1_name
            self.ai_piece = 1

        self.board = [0] * 9
        self.current_player = 1
        self.game_over = False
        self.game_over_time = 0
        self.winner = 0
        self.win_line = None
        self.winning_cells = []
        self.scores = {"X": 0, "O": 0, "D": 0}

        # Dedicated modular components
        self.ai = AIAgent() if self.mode == "ai" else None
        self.popup = VictoryPopup(w, h)

        self._layout()

        # If AI plays as X, make opening move
        if self.mode == "ai" and self.ai_piece == 1:
            self._ai_move()

    def _layout(self):
        self.bs, self.cs, self.bx, self.by = get_board_layout(self.w, self.h)
        pad = 16
        self.frame = pygame.Rect(self.bx - pad, self.by - pad,
                                 self.bs + pad * 2, self.bs + pad * 2)
        ty = TITLEBAR_H + 8
        self.btn_menu = pygame.Rect(20, ty, 110, 36)
        self.btn_restart = pygame.Rect(140, ty, 110, 36)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()
        self.popup.resize(w, h)

    def _winner(self):
        combos = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for a, b, c in combos:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                def ctr(i):
                    r, cl = i // 3, i % 3
                    return (self.bx + cl * self.cs + self.cs // 2,
                            self.by + r * self.cs + self.cs // 2)
                return self.board[a], (ctr(a), ctr(c)), [a, b, c]
        return 0, None, []

    def _check_end(self):
        w, line, cells = self._winner()
        if w:
            self.game_over, self.winner = True, w
            self.game_over_time = pygame.time.get_ticks()
            self.win_line, self.winning_cells = line, cells
            self.scores["X" if w == 1 else "O"] += 1
            self.history.add_log(w, self.mode)
        elif 0 not in self.board:
            self.game_over = True
            self.game_over_time = pygame.time.get_ticks()
            self.scores["D"] += 1
            self.history.add_log(0, self.mode)

    def _reset(self):
        next_first = self.winner if self.winner != 0 else 1
        self.board = [0] * 9
        self.current_player = next_first
        self.game_over = False
        self.game_over_time = 0
        self.winner = 0
        self.win_line = None
        self.winning_cells = []

        if self.mode == "ai" and self.ai_piece == next_first:
            self._ai_move()

    def _ai_move(self):
        if not self.ai:
            return
        pick = self.ai.get_move(self.board, self.ai_piece)
        if pick is not None:
            self.board[pick] = self.ai_piece
            self._check_end()
            if not self.game_over:
                self.current_player = 2 if self.ai_piece == 1 else 1

    def handle_click(self, pos):
        if self.btn_menu.collidepoint(pos):
            return "back"
        if self.btn_restart.collidepoint(pos):
            self._reset()
            return None

        # Victory popup interaction
        if self.game_over and pygame.time.get_ticks() - self.game_over_time > 1200:
            popup_act = self.popup.handle_click(pos)
            if popup_act == "next":
                self._reset()
            elif popup_act == "menu":
                return "back"
            elif popup_act == "exit":
                return "exit"
            return None

        # Board cell click
        x, y = pos
        if (self.bx <= x < self.bx + self.bs and self.by <= y < self.by + self.bs):
            col = int((x - self.bx) // self.cs)
            row = int((y - self.by) // self.cs)
            idx = row * 3 + col
            if 0 <= idx < 9 and self.board[idx] == 0:
                self.board[idx] = self.current_player
                self._check_end()
                if not self.game_over:
                    self.current_player = 2 if self.current_player == 1 else 1
                    if self.mode == "ai" and self.current_player == self.ai_piece:
                        self._ai_move()
        return None

    def draw(self, screen):
        m = pygame.mouse.get_pos()

        # Toolbar
        draw_button(screen, self.btn_menu, "Menu", FONT_BODY, self.btn_menu.collidepoint(m))
        draw_button(screen, self.btn_restart, "Restart", FONT_BODY, self.btn_restart.collidepoint(m))

        # Score pill
        stxt = f"{self.x_name} (X): {self.scores['X']}    {self.o_name} (O): {self.scores['O']}    Draws: {self.scores['D']}"
        ss = FONT_BODY.render(stxt, True, TEXT_BROWN)
        pill_w = ss.get_width() + 40
        sr = pygame.Rect(self.w - pill_w - 20, TITLEBAR_H + 8, pill_w, 36)
        draw_panel(screen, sr, CELL_COLOR, FRAME_COLOR, radius=10, border_w=2, shadow=False)
        screen.blit(ss, (sr.centerx - ss.get_width() // 2, sr.centery - ss.get_height() // 2))

        # Turn status pill
        if not self.game_over:
            if self.current_player == 1:
                status = f"{self.x_name}'s Turn (X)"
            else:
                status = "AI Thinking..." if (self.mode == "ai" and self.ai_piece == 2) else f"{self.o_name}'s Turn (O)"
        else:
            if self.winner == 1:
                status = f"{self.x_name} Wins!"
            elif self.winner == 2:
                status = f"{self.o_name} Wins!"
            else:
                status = "It's a Draw!"

        st_surf = FONT_HEADING.render(status, True, TEXT_CREAM)
        status_pill_w = st_surf.get_width() + 50
        status_pill = pygame.Rect(self.w // 2 - status_pill_w // 2, self.frame.y - 50, status_pill_w, 40)
        draw_panel(screen, status_pill, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=2)
        screen.blit(st_surf, (status_pill.centerx - st_surf.get_width() // 2,
                              status_pill.centery - st_surf.get_height() // 2))

        # Board frame
        draw_panel(screen, self.frame, FRAME_COLOR, FRAME_EDGE, radius=14, border_w=4)

        # Cells & wood grain
        gap = 6
        for i in range(9):
            r, c = i // 3, i % 3
            rx = self.bx + c * self.cs + gap // 2
            ry = self.by + r * self.cs + gap // 2
            rw = self.cs - gap
            cell = pygame.Rect(rx, ry, rw, rw)

            if i in self.winning_cells:
                fill = CELL_WIN
            elif self.board[i] == 0 and not self.game_over and cell.collidepoint(m):
                fill = CELL_HOVER
            else:
                fill = CELL_COLOR

            draw_panel(screen, cell, fill, FRAME_COLOR, radius=10, border_w=2, shadow=False)

            # Wood grain accent lines
            for gy in range(ry + 12, ry + rw - 8, 14):
                pygame.draw.line(screen, (fill[0] - 8, fill[1] - 8, fill[2] - 6),
                                 (rx + 8, gy), (rx + rw - 8, gy), 1)

        # Pieces
        piece_sz = int(self.cs * 0.24)
        for i in range(9):
            if self.board[i]:
                r, c = i // 3, i % 3
                cx = self.bx + c * self.cs + self.cs // 2
                cy = self.by + r * self.cs + self.cs // 2
                if self.board[i] == 1:
                    draw_x(screen, cx, cy, piece_sz)
                else:
                    draw_o(screen, cx, cy, piece_sz)

        # Winning strike line
        if self.win_line:
            p1, p2 = self.win_line
            pygame.draw.line(screen, GOLD, p1, p2, 8)
            pygame.draw.line(screen, GOLD_LIGHT, p1, p2, 3)

        # Victory popup modal
        if self.game_over and pygame.time.get_ticks() - self.game_over_time > 1200:
            self.popup.draw(screen, self.winner, self.x_name, self.o_name, self.scores)

        # History drawer overlay on top
        self.history.draw(screen)
