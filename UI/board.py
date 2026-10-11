import pygame
from constants import TITLEBAR_H, get_board_layout
from popup import VictoryPopup
from ai_agent import AIAgent
from board_view import BoardView
from game_state import GameState


class GameBoard:
    """Game controller coordinating screen layout, user clicks, AI, and views."""

    def __init__(self, w, h, mode, p1_name, p2_name, p1_piece, history):
        self.w, self.h = w, h
        self.history = history
        self.state = GameState(mode, p1_name, p2_name, p1_piece)

        self.ai = AIAgent() if mode == "ai" else None
        self.popup = VictoryPopup(w, h)

        self._layout()
        if mode == "ai" and self.state.ai_piece == 1:
            self._ai_move()

    # Convenience properties forwarding to self.state for compatibility
    @property
    def board(self): return self.state.board
    @property
    def mode(self): return self.state.mode
    @property
    def x_name(self): return self.state.x_name
    @property
    def o_name(self): return self.state.o_name
    @property
    def scores(self): return self.state.scores
    @property
    def current_player(self): return self.state.current_player
    @property
    def game_over(self): return self.state.game_over
    @property
    def winner(self): return self.state.winner

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

    def _win_line(self):
        if not self.state.win_cells:
            return None
        def ctr(i):
            return (self.bx + (i % 3) * self.cs + self.cs // 2,
                    self.by + (i // 3) * self.cs + self.cs // 2)
        return ctr(self.state.win_cells[0]), ctr(self.state.win_cells[2])

    def _reset(self):
        next_first = self.state.reset()
        if self.state.mode == "ai" and self.state.ai_piece == next_first:
            self._ai_move()

    def _ai_move(self):
        if not self.ai:
            return
        pick = self.ai.get_move(self.state.board, self.state.ai_piece)
        if pick is not None:
            _, outcome = self.state.make_move(pick, pygame.time.get_ticks())
            if outcome is not None:
                self.history.add_log(outcome, self.state.mode)

    def handle_click(self, pos):
        if self.btn_menu.collidepoint(pos):
            return "back"
        if self.btn_restart.collidepoint(pos):
            self._reset()
            return None

        # Victory popup interaction
        if self.state.game_over and pygame.time.get_ticks() - self.state.game_over_time > 1200:
            act = self.popup.handle_click(pos)
            if act == "next":
                self._reset()
            elif act in ("menu", "exit"):
                return "back" if act == "menu" else "exit"
            return None

        # Board cell click
        x, y = pos
        if (self.bx <= x < self.bx + self.bs and self.by <= y < self.by + self.bs):
            idx = int((y - self.by) // self.cs) * 3 + int((x - self.bx) // self.cs)
            ok, outcome = self.state.make_move(idx, pygame.time.get_ticks())
            if ok:
                if outcome is not None:
                    self.history.add_log(outcome, self.state.mode)
                elif self.state.mode == "ai" and self.state.current_player == self.state.ai_piece:
                    self._ai_move()
        return None

    def draw(self, screen):
        m = pygame.mouse.get_pos()
        st = self.state

        BoardView.draw_toolbar(screen, self.btn_menu, self.btn_restart, m)
        BoardView.draw_score_pill(screen, self.w, st.x_name, st.o_name, st.scores)
        BoardView.draw_status_pill(screen, self.w, self.frame.y, st.game_over, st.winner,
                                   st.current_player, st.x_name, st.o_name, st.mode, st.ai_piece)
        BoardView.draw_grid_and_pieces(screen, st.board, self.frame, self.bx, self.by, self.bs, self.cs,
                                       st.win_cells, st.game_over, m)
        BoardView.draw_win_line(screen, self._win_line())

        if st.game_over and pygame.time.get_ticks() - st.game_over_time > 1200:
            self.popup.draw(screen, st.winner, st.x_name, st.o_name, st.scores)

        self.history.draw(screen)
