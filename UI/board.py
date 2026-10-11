import pygame
from constants import TITLEBAR_H, get_board_layout
from popup import VictoryPopup
from ai_agent import AIAgent
from board_view import BoardView


class GameBoard:
    """Game controller coordinating board state, player input, AI, and views."""

    def __init__(self, w, h, mode, p1_name, p2_name, p1_piece, history):
        self.w, self.h = w, h
        self.mode = mode
        self.history = history
        self.p1_name = p1_name.strip() if p1_name.strip() else "Player 1"
        self.p2_name = p2_name.strip() if p2_name.strip() else ("AI" if mode == "ai" else "Player 2")
        self.p1_piece = p1_piece

        # Determine roles based on P1's piece selection
        if p1_piece == "X":
            self.x_name, self.o_name = self.p1_name, self.p2_name
            self.ai_piece = 2
        else:
            self.x_name, self.o_name = self.p2_name, self.p1_name
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
        self.frame = pygame.Rect(self.bx - pad, self.by - pad, self.bs + pad * 2, self.bs + pad * 2)
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
                    return (self.bx + (i % 3) * self.cs + self.cs // 2,
                            self.by + (i // 3) * self.cs + self.cs // 2)
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
            idx = int((y - self.by) // self.cs) * 3 + int((x - self.bx) // self.cs)
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

        # View rendering delegated to BoardView
        BoardView.draw_toolbar(screen, self.btn_menu, self.btn_restart, m)
        BoardView.draw_score_pill(screen, self.w, self.x_name, self.o_name, self.scores)
        BoardView.draw_status_pill(screen, self.w, self.frame.y, self.game_over, self.winner,
                                   self.current_player, self.x_name, self.o_name, self.mode, self.ai_piece)
        BoardView.draw_grid_and_pieces(screen, self.board, self.frame, self.bx, self.by, self.bs, self.cs,
                                       self.winning_cells, self.game_over, m)
        BoardView.draw_win_line(screen, self.win_line)

        # Overlays
        if self.game_over and pygame.time.get_ticks() - self.game_over_time > 1200:
            self.popup.draw(screen, self.winner, self.x_name, self.o_name, self.scores)

        self.history.draw(screen)
