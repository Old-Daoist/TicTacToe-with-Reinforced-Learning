import pygame
from constants import (
    TITLEBAR_H, FRAME_COLOR, FRAME_EDGE, CELL_COLOR, CELL_HOVER, CELL_WIN,
    TEXT_BROWN, TEXT_CREAM, GOLD, GOLD_LIGHT, FONT_HEADING, FONT_BODY
)
from utils import draw_panel, draw_button
from pieces import draw_x, draw_o


class BoardView:
    """Handles rendering of toolbar, score pill, status pill, grid cells, and strike line."""

    @staticmethod
    def draw_toolbar(screen, btn_menu, btn_restart, mouse_pos):
        draw_button(screen, btn_menu, "Menu", FONT_BODY, btn_menu.collidepoint(mouse_pos))
        draw_button(screen, btn_restart, "Restart", FONT_BODY, btn_restart.collidepoint(mouse_pos))

    @staticmethod
    def draw_score_pill(screen, w, x_name, o_name, scores):
        stxt = f"{x_name} (X): {scores['X']}    {o_name} (O): {scores['O']}    Draws: {scores['D']}"
        ss = FONT_BODY.render(stxt, True, TEXT_BROWN)
        pill_w = ss.get_width() + 40
        sr = pygame.Rect(w - pill_w - 20, TITLEBAR_H + 8, pill_w, 36)
        draw_panel(screen, sr, CELL_COLOR, FRAME_COLOR, radius=10, border_w=2, shadow=False)
        screen.blit(ss, (sr.centerx - ss.get_width() // 2, sr.centery - ss.get_height() // 2))

    @staticmethod
    def draw_status_pill(screen, w, frame_y, game_over, winner, current_player, x_name, o_name, mode, ai_piece):
        if not game_over:
            if current_player == 1:
                status = f"{x_name}'s Turn (X)"
            else:
                status = "AI Thinking..." if (mode == "ai" and ai_piece == 2) else f"{o_name}'s Turn (O)"
        else:
            if winner == 1:
                status = f"{x_name} Wins!"
            elif winner == 2:
                status = f"{o_name} Wins!"
            else:
                status = "It's a Draw!"

        st_surf = FONT_HEADING.render(status, True, TEXT_CREAM)
        status_pill_w = st_surf.get_width() + 50
        status_pill = pygame.Rect(w // 2 - status_pill_w // 2, frame_y - 50, status_pill_w, 40)
        draw_panel(screen, status_pill, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=2)
        screen.blit(st_surf, (status_pill.centerx - st_surf.get_width() // 2,
                              status_pill.centery - st_surf.get_height() // 2))

    @staticmethod
    def draw_grid_and_pieces(screen, board, frame, bx, by, bs, cs, winning_cells, game_over, mouse_pos):
        # Outer board frame
        draw_panel(screen, frame, FRAME_COLOR, FRAME_EDGE, radius=14, border_w=4)

        # Cells & wood grain
        gap = 6
        for i in range(9):
            r, c = i // 3, i % 3
            rx = bx + c * cs + gap // 2
            ry = by + r * cs + gap // 2
            rw = cs - gap
            cell = pygame.Rect(rx, ry, rw, rw)

            if i in winning_cells:
                fill = CELL_WIN
            elif board[i] == 0 and not game_over and cell.collidepoint(mouse_pos):
                fill = CELL_HOVER
            else:
                fill = CELL_COLOR

            draw_panel(screen, cell, fill, FRAME_COLOR, radius=10, border_w=2, shadow=False)

            # Wood grain accent lines
            for gy in range(ry + 12, ry + rw - 8, 14):
                pygame.draw.line(screen, (fill[0] - 8, fill[1] - 8, fill[2] - 6),
                                 (rx + 8, gy), (rx + rw - 8, gy), 1)

        # Pieces
        piece_sz = int(cs * 0.24)
        for i in range(9):
            if board[i]:
                cx = bx + (i % 3) * cs + cs // 2
                cy = by + (i // 3) * cs + cs // 2
                if board[i] == 1:
                    draw_x(screen, cx, cy, piece_sz)
                else:
                    draw_o(screen, cx, cy, piece_sz)

    @staticmethod
    def draw_win_line(screen, win_line):
        if win_line:
            p1, p2 = win_line
            pygame.draw.line(screen, GOLD, p1, p2, 8)
            pygame.draw.line(screen, GOLD_LIGHT, p1, p2, 3)
