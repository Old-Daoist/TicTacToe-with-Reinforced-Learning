import pygame
import random
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    import torch
    from network import TicTacToeNetwork
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from constants import *
from utils import draw_panel, draw_button


class GameBoard:
    """The main game screen with a clean layout:
       Toolbar -> Status pill -> Centered board -> Score footer
       History drawer overlays from the right."""

    def __init__(self, w, h, mode, p1_name, p2_name, p1_piece, history):
        self.w, self.h = w, h
        self.mode = mode
        self.history = history
        self.p1_name = p1_name if p1_name.strip() else "Player 1"
        self.p2_name = p2_name if p2_name.strip() else ("AI" if mode == "ai" else "Player 2")
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
        self.network = None
        self._layout()
        self._load_ai()

        # If AI is playing as X, it needs to make the very first move!
        if self.mode == "ai" and self.ai_piece == 1:
            self._ai_move()

    # ---- layout ----
    def _layout(self):
        self.bs, self.cs, self.bx, self.by = get_board_layout(self.w, self.h)
        pad = 16
        self.frame = pygame.Rect(self.bx - pad, self.by - pad,
                                 self.bs + pad * 2, self.bs + pad * 2)
        # toolbar buttons (below the title bar)
        ty = TITLEBAR_H + 8
        self.btn_menu = pygame.Rect(20, ty, 110, 36)
        self.btn_restart = pygame.Rect(140, ty, 110, 36)

    def resize(self, w, h):
        self.w, self.h = w, h
        self._layout()

    # ---- AI ----
    def _load_ai(self):
        if not TORCH_AVAILABLE or self.mode != "ai":
            return
        p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tictactoe_model.pth")
        if os.path.exists(p):
            try:
                self.network = TicTacToeNetwork()
                self.network.load_state_dict(torch.load(p, map_location="cpu", weights_only=True))
                self.network.eval()
            except Exception:
                self.network = None

    # ---- game logic ----
    def _winner(self):
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a, b, c in combos:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                def ctr(i):
                    r, cl = i // 3, i % 3
                    return (self.bx + cl * self.cs + self.cs // 2,
                            self.by + r * self.cs + self.cs // 2)
                return self.board[a], (ctr(a), ctr(c)), [a, b, c]
        return 0, None, []

    def _ai_move(self):
        empty = [i for i in range(9) if self.board[i] == 0]
        if not empty:
            return
        pick = -1
        if self.network:
            try:
                # The AI was trained with its pieces as 1 and opponent as -1
                obs = [1 if x == self.ai_piece else -1 if x != 0 else 0 for x in self.board]
                with torch.no_grad():
                    q = self.network(torch.tensor(obs, dtype=torch.float32))
                pick = empty[torch.argmax(q[empty]).item()]
            except Exception:
                pass
        if pick < 0:
            pick = random.choice(empty)
        self.board[pick] = self.ai_piece
        self._check_end()
        if not self.game_over:
            self.current_player = 2 if self.ai_piece == 1 else 1

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
        next_first = 1
        if self.winner != 0:
            next_first = self.winner
            
        self.board = [0] * 9
        self.current_player = next_first
        self.game_over = False
        self.game_over_time = 0
        self.winner = 0
        self.win_line = self.winning_cells = None
        self.winning_cells = []
        
        # If AI is playing as next_first, it moves first again
        if self.mode == "ai" and self.ai_piece == next_first:
            self._ai_move()

    # ---- input ----
    def handle_click(self, pos):
        if self.btn_menu.collidepoint(pos):
            return "back"
        if self.btn_restart.collidepoint(pos):
            self._reset()
            return None

        # If game is over, check for buttons on the popup
        if self.game_over:
            if pygame.time.get_ticks() - self.game_over_time > 1200:
                btn_next, btn_menu, btn_exit = self._get_popup_btns()
                if btn_next.collidepoint(pos):
                    self._reset()
                elif btn_menu.collidepoint(pos):
                    return "back"
                elif btn_exit.collidepoint(pos):
                    return "exit"
            return None

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

    def _get_popup_btns(self):
        """Returns the rects for the (Next, Menu, Exit) buttons on the victory popup."""
        pw, ph = 480, 340
        py = self.h // 2 - ph // 2
        btn_w, btn_h = 130, 45
        gap = 15
        
        # Center the three buttons
        bx2 = self.w // 2 - btn_w // 2
        bx1 = bx2 - btn_w - gap
        bx3 = bx2 + btn_w + gap
        
        y = py + ph - 80
        return pygame.Rect(bx1, y, btn_w, btn_h), pygame.Rect(bx2, y, btn_w, btn_h), pygame.Rect(bx3, y, btn_w, btn_h)

    # ---- drawing ----
    def _draw_x(self, screen, cx, cy, sz):
        t = max(6, sz // 5)
        off = sz
        # carved shadow
        pygame.draw.line(screen, X_DARK, (cx-off+2,cy-off+2),(cx+off+2,cy+off+2), t+3)
        pygame.draw.line(screen, X_DARK, (cx+off+2,cy-off+2),(cx-off+2,cy+off+2), t+3)
        # main
        pygame.draw.line(screen, X_LIGHT, (cx-off,cy-off),(cx+off,cy+off), t)
        pygame.draw.line(screen, X_LIGHT, (cx+off,cy-off),(cx-off,cy+off), t)

    def _draw_o(self, screen, cx, cy, sz):
        t = max(6, sz // 5)
        r = sz + 4
        pygame.draw.circle(screen, O_DARK, (cx+2, cy+2), r, t+3)
        pygame.draw.circle(screen, O_LIGHT, (cx, cy), r, t)

    def _draw_victory_popup(self, screen):
        """Draws a beautiful trophy popup over the board when the game ends."""
        # Dim the background
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Popup card
        pw, ph = 480, 340
        px = self.w // 2 - pw // 2
        py = self.h // 2 - ph // 2
        popup = pygame.Rect(px, py, pw, ph)

        # Outer frame
        draw_panel(screen, popup, FRAME_COLOR, FRAME_EDGE, radius=22, border_w=4)
        # Inner lighter area
        inner = pygame.Rect(px + 10, py + 10, pw - 20, ph - 20)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=18, border_w=2, shadow=False)

        # Trophy / emoji text
        try:
            emoji_font = pygame.font.SysFont("segoeuiemoji", 64)
        except Exception:
            emoji_font = pygame.font.Font(None, 72)

        if self.winner == 1:
            trophy = emoji_font.render("🏆", True, TEXT_BROWN)
            title = f"{self.x_name} Wins!"
        elif self.winner == 2:
            trophy = emoji_font.render("🏆", True, TEXT_BROWN)
            title = f"{self.o_name} Wins!"
        else:
            trophy = emoji_font.render("🤝", True, TEXT_BROWN)
            title = "It's a Draw!"

        screen.blit(trophy, (self.w // 2 - trophy.get_width() // 2, py + 30))

        # Title
        title_surf = FONT_HEADING.render(title, True, TEXT_BROWN)
        screen.blit(title_surf, (self.w // 2 - title_surf.get_width() // 2, py + 115))

        # Divider
        pygame.draw.line(screen, FRAME_COLOR, (px + 40, py + 165), (px + pw - 40, py + 165), 2)

        # Score summary
        score_lines = [
            f"Player X:  {self.scores['X']}",
            f"Player O:  {self.scores['O']}",
            f"Draws:       {self.scores['D']}"
        ]
        y_off = py + 180
        for line in score_lines:
            s = FONT_BODY.render(line, True, TEXT_BROWN)
            screen.blit(s, (self.w // 2 - s.get_width() // 2, y_off))
            y_off += 28

        # Buttons
        m = pygame.mouse.get_pos()
        btn_next, btn_menu, btn_exit = self._get_popup_btns()
        draw_button(screen, btn_next, "Next Game", FONT_BODY, btn_next.collidepoint(m))
        draw_button(screen, btn_menu, "Main Menu", FONT_BODY, btn_menu.collidepoint(m))
        draw_button(screen, btn_exit, "Exit", FONT_BODY, btn_exit.collidepoint(m))

    def draw(self, screen):
        m = pygame.mouse.get_pos()

        # ---- toolbar ----
        draw_button(screen, self.btn_menu, "Menu", FONT_BODY, self.btn_menu.collidepoint(m))
        draw_button(screen, self.btn_restart, "Restart", FONT_BODY, self.btn_restart.collidepoint(m))

        # ---- score (right side of toolbar) ----
        stxt = f"{self.x_name} (X): {self.scores['X']}    {self.o_name} (O): {self.scores['O']}    Draws: {self.scores['D']}"
        ss = FONT_BODY.render(stxt, True, TEXT_BROWN)
        pill_w = ss.get_width() + 40
        sr = pygame.Rect(self.w - pill_w - 20, TITLEBAR_H + 8, pill_w, 36)
        draw_panel(screen, sr, CELL_COLOR, FRAME_COLOR, radius=10, border_w=2, shadow=False)
        screen.blit(ss, (sr.centerx - ss.get_width()//2, sr.centery - ss.get_height()//2))

        # ---- status pill (centered above board) ----
        if not self.game_over:
            if self.current_player == 1:
                status = f"{self.x_name}'s Turn (X)"
            else:
                if self.mode == "ai" and self.ai_piece == 2:
                    status = "AI Thinking..."
                else:
                    status = f"{self.o_name}'s Turn (O)"
        else:
            if self.winner == 1:
                status = f"{self.x_name} Wins!"
            elif self.winner == 2:
                status = f"{self.o_name} Wins!"
            else:
                status = "It's a Draw!"

        st_surf = FONT_HEADING.render(status, True, TEXT_CREAM)
        pill_w = st_surf.get_width() + 50
        pill = pygame.Rect(self.w // 2 - pill_w // 2, self.frame.y - 50, pill_w, 40)
        draw_panel(screen, pill, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=2)
        screen.blit(st_surf, (pill.centerx - st_surf.get_width()//2,
                              pill.centery - st_surf.get_height()//2))

        # ---- board frame ----
        draw_panel(screen, self.frame, FRAME_COLOR, FRAME_EDGE, radius=14, border_w=4)

        # ---- cells ----
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

            # Wood grain: a few thin horizontal lines
            for gy in range(ry + 12, ry + rw - 8, 14):
                pygame.draw.line(screen, (fill[0]-8, fill[1]-8, fill[2]-6),
                                 (rx + 8, gy), (rx + rw - 8, gy), 1)

        # ---- pieces ----
        piece_sz = int(self.cs * 0.24)
        for i in range(9):
            if self.board[i]:
                r, c = i // 3, i % 3
                cx = self.bx + c * self.cs + self.cs // 2
                cy = self.by + r * self.cs + self.cs // 2
                if self.board[i] == 1:
                    self._draw_x(screen, cx, cy, piece_sz)
                else:
                    self._draw_o(screen, cx, cy, piece_sz)

        # ---- winning line ----
        if self.win_line:
            p1, p2 = self.win_line
            pygame.draw.line(screen, GOLD, p1, p2, 8)
            pygame.draw.line(screen, GOLD_LIGHT, p1, p2, 3)

        # ---- victory / draw popup ----
        if self.game_over and pygame.time.get_ticks() - self.game_over_time > 1200:
            self._draw_victory_popup(screen)

        # ---- history (on top of everything) ----
        self.history.draw(screen)

