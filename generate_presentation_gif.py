import os
import sys
import math
import shutil
from PIL import Image

# Setup paths
workspace_dir = "/home/kunal/Desktop/TicTacToe-with-Reinforced-Learning"
ui_dir = os.path.join(workspace_dir, "UI")
sys.path.insert(0, workspace_dir)
sys.path.insert(0, ui_dir)

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

from constants import *
from utils import create_bg, draw_panel, draw_button
from board_view import BoardView
from popup import VictoryPopup
from menu import MainMenu
from ai_agent import AIAgent
from game_state import GameState

def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(t * math.pi)

def draw_cursor(surface, pos, clicking=False):
    x, y = int(pos[0]), int(pos[1])
    if clicking:
        x += 1
        y += 1
    # Sleek OS pointer arrow
    pts = [
        (x, y),
        (x, y + 21),
        (x + 5, y + 16),
        (x + 10, y + 26),
        (x + 14, y + 24),
        (x + 9, y + 15),
        (x + 16, y + 15)
    ]
    # Drop shadow
    shadow_pts = [(px + 3, py + 3) for px, py in pts]
    pygame.draw.polygon(surface, (0, 0, 0, 70), shadow_pts)
    # Border
    pygame.draw.polygon(surface, (20, 20, 20), pts)
    # Fill
    inner_pts = [
        (x + 1, y + 2),
        (x + 1, y + 18),
        (x + 5, y + 14),
        (x + 9, y + 23),
        (x + 12, y + 22),
        (x + 8, y + 14),
        (x + 14, y + 14)
    ]
    fill_col = (205, 205, 205) if clicking else (255, 255, 255)
    pygame.draw.polygon(surface, fill_col, inner_pts)

def get_cell_center(idx, bx, by, cs):
    r, c = idx // 3, idx % 3
    return (bx + c * cs + cs // 2, by + r * cs + cs // 2)

def generate_gameplay_gif():
    print("\n--- Generating tictactoe_gameplay.gif ---")
    w, h = DEFAULT_W, DEFAULT_H
    screen = pygame.Surface((w, h))
    bg = create_bg(w, h)
    
    bs, cs, bx, by = get_board_layout(w, h)
    pad = 16
    frame = pygame.Rect(bx - pad, by - pad, bs + pad * 2, bs + pad * 2)
    ty = TITLEBAR_H + 8
    btn_menu = pygame.Rect(20, ty, 110, 36)
    btn_restart = pygame.Rect(140, ty, 110, 36)
    popup = VictoryPopup(w, h)
    ai = AIAgent()

    state = GameState("ai", "Player", "RL Agent", "X")
    frames = []

    def capture(mouse_pos, clicking=False, show_popup=False, is_ai_thinking=False, win_line_points=None):
        screen.blit(bg, (0, 0))
        
        # Toolbar
        BoardView.draw_toolbar(screen, btn_menu, btn_restart, mouse_pos)
        
        # Score Pill
        BoardView.draw_score_pill(screen, w, state.x_name, state.o_name, state.scores)
        
        # Status Pill
        if is_ai_thinking and not state.game_over:
            st_surf = FONT_HEADING.render("AI Thinking...", True, TEXT_CREAM)
            pill_w = st_surf.get_width() + 50
            status_pill = pygame.Rect(w // 2 - pill_w // 2, frame.y - 50, pill_w, 40)
            draw_panel(screen, status_pill, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=2)
            screen.blit(st_surf, (status_pill.centerx - st_surf.get_width() // 2,
                                  status_pill.centery - st_surf.get_height() // 2))
        else:
            BoardView.draw_status_pill(screen, w, frame.y, state.game_over, state.winner,
                                       state.current_player, state.x_name, state.o_name, state.mode, state.ai_piece)
            
        # Board & Pieces
        BoardView.draw_grid_and_pieces(screen, state.board, frame, bx, by, bs, cs,
                                       state.win_cells, state.game_over, mouse_pos)
        
        # Win Line
        if win_line_points is not None:
            BoardView.draw_win_line(screen, win_line_points)

        # Victory Popup
        if show_popup:
            popup.draw(screen, state.winner, state.x_name, state.o_name, state.scores)

        # Draw Cursor
        draw_cursor(screen, mouse_pos, clicking=clicking)

        # Convert to PIL and super-sample resize to 960x614
        raw = pygame.image.tostring(screen, "RGB")
        img = Image.frombytes("RGB", (w, h), raw)
        img_resized = img.resize((960, 614), Image.Resampling.LANCZOS)
        frames.append(img_resized)

    # Initial state
    cur_pos = (bx - 70, by + 100)

    # 1. Opening freeze (0.6s)
    for _ in range(8):
        capture(cur_pos)

    turn_plan = [
        ("player", 0),  # Corner opening
        ("ai", 4),      # AI takes center
        ("player", 8),  # Opposite corner
        ("ai", 1),      # AI takes top-edge
        ("player", 3),  # Player tries left-edge
        ("ai", 7)       # AI takes bottom-edge -> vertical win [1, 4, 7]!
    ]

    for turn_type, target_cell in turn_plan:
        target_pos = get_cell_center(target_cell, bx, by, cs)
        
        if turn_type == "player":
            # Smooth cursor gliding to cell (6 frames)
            start_pos = cur_pos
            steps = 7
            for s in range(1, steps + 1):
                t = ease_in_out(s / steps)
                px = start_pos[0] + (target_pos[0] - start_pos[0]) * t
                py = start_pos[1] + (target_pos[1] - start_pos[1]) * t
                cur_pos = (px, py)
                capture(cur_pos)
            
            # Hover over cell (3 frames)
            for _ in range(3):
                capture(cur_pos)
            
            # Click down (2 frames)
            capture(cur_pos, clicking=True)
            capture(cur_pos, clicking=True)
            
            # Execute player move
            state.make_move(target_cell)
            
            # Release click and show AI thinking state (3 frames)
            for _ in range(3):
                capture(cur_pos, clicking=False, is_ai_thinking=True)
            
        else: # AI Turn
            # Cursor drifts slightly away during AI deliberation (5 frames)
            cursor_rest = (cur_pos[0] + 50, cur_pos[1] + 35)
            for s in range(1, 5):
                t = ease_in_out(s / 4)
                px = cur_pos[0] + (cursor_rest[0] - cur_pos[0]) * t
                py = cur_pos[1] + (cursor_rest[1] - cur_pos[1]) * t
                capture((px, py), is_ai_thinking=True)
            cur_pos = cursor_rest
            
            # Thinking pause (3 frames)
            for _ in range(3):
                capture(cur_pos, is_ai_thinking=True)
            
            # Real AI DQN model selects move
            real_ai_move = ai.get_move(state.board, state.ai_piece)
            actual_move = real_ai_move if real_ai_move is not None else target_cell
            state.make_move(actual_move)
            
            # Placement frame (4 frames)
            for _ in range(4):
                capture(cur_pos)

    # Strike Line Animation!
    # Compute extended start and end for cinematic strike
    p1 = get_cell_center(state.win_cells[0], bx, by, cs)
    p2 = get_cell_center(state.win_cells[2], bx, by, cs)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = math.hypot(dx, dy)
    ext = 40  # extend 40px beyond centers
    ux = dx / dist if dist else 0
    uy = dy / dist if dist else 1
    ext_start = (p1[0] - ux * ext, p1[1] - uy * ext)
    ext_end = (p2[0] + ux * ext, p2[1] + uy * ext)

    # Animate line drawing from ext_start to ext_end (8 frames)
    strike_steps = 8
    for s in range(1, strike_steps + 1):
        t = ease_in_out(s / strike_steps)
        curr_pt = (ext_start[0] + (ext_end[0] - ext_start[0]) * t,
                   ext_start[1] + (ext_end[1] - ext_start[1]) * t)
        capture(cur_pos, win_line_points=(ext_start, curr_pt))

    # Hold golden winning board and strike line (12 frames ~ 0.85s)
    for _ in range(12):
        capture(cur_pos, win_line_points=(ext_start, ext_end))

    # Now show victory popup modal
    popup_btns = popup.get_buttons()
    btn_next = popup_btns[0]
    next_center = (btn_next.centerx, btn_next.centery)

    # Cursor glides toward "Next Game" button (8 frames)
    start_pos = cur_pos
    steps = 8
    for s in range(1, steps + 1):
        t = ease_in_out(s / steps)
        px = start_pos[0] + (next_center[0] - start_pos[0]) * t
        py = start_pos[1] + (next_center[1] - start_pos[1]) * t
        cur_pos = (px, py)
        capture(cur_pos, show_popup=True, win_line_points=(ext_start, ext_end))

    # Hover on "Next Game" button (holding celebratory state for 24 frames ~ 1.7s)
    for _ in range(24):
        capture(cur_pos, show_popup=True, win_line_points=(ext_start, ext_end))

    # Click "Next Game" (2 frames)
    capture(cur_pos, clicking=True, show_popup=True, win_line_points=(ext_start, ext_end))
    capture(cur_pos, clicking=True, show_popup=True, win_line_points=(ext_start, ext_end))

    print(f"Total gameplay frames: {len(frames)}")

    output_gif = os.path.join(workspace_dir, "tictactoe_gameplay.gif")
    copy_gif = os.path.join(workspace_dir, "tictactoe.gif")

    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=70,
        loop=0
    )
    shutil.copyfile(output_gif, copy_gif)
    print(f"Saved: {output_gif} ({os.path.getsize(output_gif)/(1024*1024):.2f} MB)")


def generate_full_showcase_gif():
    print("\n--- Generating tictactoe_full_showcase.gif (with Main Menu intro) ---")
    w, h = DEFAULT_W, DEFAULT_H
    screen = pygame.Surface((w, h))
    bg = create_bg(w, h)
    menu = MainMenu(w, h)
    
    bs, cs, bx, by = get_board_layout(w, h)
    pad = 16
    frame = pygame.Rect(bx - pad, by - pad, bs + pad * 2, bs + pad * 2)
    ty = TITLEBAR_H + 8
    btn_menu = pygame.Rect(20, ty, 110, 36)
    btn_restart = pygame.Rect(140, ty, 110, 36)
    popup = VictoryPopup(w, h)
    ai = AIAgent()

    state = GameState("ai", "Player", "RL Agent", "X")
    frames = []

    def capture_menu(mouse_pos, clicking=False):
        screen.blit(bg, (0, 0))
        # Draw Main Menu
        draw_panel(screen, menu.panel, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=4)
        inner = pygame.Rect(menu.panel.x + 12, menu.panel.y + 12,
                            menu.panel.width - 24, menu.panel.height - 24)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=16, border_w=2, shadow=False)
        t = FONT_TITLE.render("TIC-TAC-TOE", True, TEXT_BROWN)
        screen.blit(t, (w // 2 - t.get_width() // 2, menu.panel.y + 40))
        ly = menu.panel.y + 120
        pygame.draw.line(screen, FRAME_COLOR,
                         (menu.panel.x + 50, ly), (menu.panel.x + menu.panel.width - 50, ly), 2)
        sub = FONT_BODY.render("Select Game Mode", True, TEXT_BROWN)
        screen.blit(sub, (w // 2 - sub.get_width() // 2, ly + 12))
        
        # Buttons
        draw_button(screen, menu.btn_ai, "Player  vs  AI", FONT_HEADING, menu.btn_ai.collidepoint(mouse_pos))
        draw_button(screen, menu.btn_pvp, "Player  vs  Player", FONT_HEADING, menu.btn_pvp.collidepoint(mouse_pos))
        draw_button(screen, menu.btn_exit, "Exit Game", FONT_HEADING, menu.btn_exit.collidepoint(mouse_pos))
        
        draw_cursor(screen, mouse_pos, clicking=clicking)
        raw = pygame.image.tostring(screen, "RGB")
        img = Image.frombytes("RGB", (w, h), raw)
        frames.append(img.resize((960, 614), Image.Resampling.LANCZOS))

    def capture_board(mouse_pos, clicking=False, show_popup=False, is_ai_thinking=False, win_line_points=None):
        screen.blit(bg, (0, 0))
        BoardView.draw_toolbar(screen, btn_menu, btn_restart, mouse_pos)
        BoardView.draw_score_pill(screen, w, state.x_name, state.o_name, state.scores)
        if is_ai_thinking and not state.game_over:
            st_surf = FONT_HEADING.render("AI Thinking...", True, TEXT_CREAM)
            pill_w = st_surf.get_width() + 50
            status_pill = pygame.Rect(w // 2 - pill_w // 2, frame.y - 50, pill_w, 40)
            draw_panel(screen, status_pill, FRAME_COLOR, FRAME_EDGE, radius=20, border_w=2)
            screen.blit(st_surf, (status_pill.centerx - st_surf.get_width() // 2,
                                  status_pill.centery - st_surf.get_height() // 2))
        else:
            BoardView.draw_status_pill(screen, w, frame.y, state.game_over, state.winner,
                                       state.current_player, state.x_name, state.o_name, state.mode, state.ai_piece)
            
        BoardView.draw_grid_and_pieces(screen, state.board, frame, bx, by, bs, cs,
                                       state.win_cells, state.game_over, mouse_pos)
        if win_line_points is not None:
            BoardView.draw_win_line(screen, win_line_points)
        if show_popup:
            popup.draw(screen, state.winner, state.x_name, state.o_name, state.scores)
        draw_cursor(screen, mouse_pos, clicking=clicking)
        raw = pygame.image.tostring(screen, "RGB")
        img = Image.frombytes("RGB", (w, h), raw)
        frames.append(img.resize((960, 614), Image.Resampling.LANCZOS))

    # Phase 1: Main Menu
    cur_pos = (menu.btn_ai.centerx - 120, menu.btn_ai.centery + 100)
    for _ in range(6):
        capture_menu(cur_pos)
    
    # Cursor glides to "Player vs AI"
    start_pos = cur_pos
    ai_btn_center = (menu.btn_ai.centerx, menu.btn_ai.centery)
    for s in range(1, 8):
        t = ease_in_out(s / 7)
        px = start_pos[0] + (ai_btn_center[0] - start_pos[0]) * t
        py = start_pos[1] + (ai_btn_center[1] - start_pos[1]) * t
        cur_pos = (px, py)
        capture_menu(cur_pos)
    
    # Hover (3 frames)
    for _ in range(3):
        capture_menu(cur_pos)
    # Click (2 frames)
    capture_menu(cur_pos, clicking=True)
    capture_menu(cur_pos, clicking=True)

    # Phase 2: Board Gameplay
    cur_pos = (bx - 70, by + 100)
    for _ in range(6):
        capture_board(cur_pos)

    turn_plan = [
        ("player", 0),
        ("ai", 4),
        ("player", 8),
        ("ai", 1),
        ("player", 3),
        ("ai", 7)
    ]

    for turn_type, target_cell in turn_plan:
        target_pos = get_cell_center(target_cell, bx, by, cs)
        if turn_type == "player":
            start_pos = cur_pos
            steps = 6
            for s in range(1, steps + 1):
                t = ease_in_out(s / steps)
                px = start_pos[0] + (target_pos[0] - start_pos[0]) * t
                py = start_pos[1] + (target_pos[1] - start_pos[1]) * t
                cur_pos = (px, py)
                capture_board(cur_pos)
            for _ in range(2):
                capture_board(cur_pos)
            capture_board(cur_pos, clicking=True)
            capture_board(cur_pos, clicking=True)
            state.make_move(target_cell)
            for _ in range(3):
                capture_board(cur_pos, clicking=False, is_ai_thinking=True)
        else:
            cursor_rest = (cur_pos[0] + 40, cur_pos[1] + 30)
            for s in range(1, 4):
                t = ease_in_out(s / 3)
                px = cur_pos[0] + (cursor_rest[0] - cur_pos[0]) * t
                py = cur_pos[1] + (cursor_rest[1] - cur_pos[1]) * t
                capture_board((px, py), is_ai_thinking=True)
            cur_pos = cursor_rest
            for _ in range(2):
                capture_board(cur_pos, is_ai_thinking=True)
            real_ai_move = ai.get_move(state.board, state.ai_piece)
            state.make_move(real_ai_move if real_ai_move is not None else target_cell)
            for _ in range(3):
                capture_board(cur_pos)

    # Strike Line
    p1 = get_cell_center(state.win_cells[0], bx, by, cs)
    p2 = get_cell_center(state.win_cells[2], bx, by, cs)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = math.hypot(dx, dy)
    ext = 40
    ux = dx / dist if dist else 0
    uy = dy / dist if dist else 1
    ext_start = (p1[0] - ux * ext, p1[1] - uy * ext)
    ext_end = (p2[0] + ux * ext, p2[1] + uy * ext)

    for s in range(1, 7):
        t = ease_in_out(s / 6)
        curr_pt = (ext_start[0] + (ext_end[0] - ext_start[0]) * t,
                   ext_start[1] + (ext_end[1] - ext_start[1]) * t)
        capture_board(cur_pos, win_line_points=(ext_start, curr_pt))

    for _ in range(8):
        capture_board(cur_pos, win_line_points=(ext_start, ext_end))

    # Popup
    popup_btns = popup.get_buttons()
    btn_next = popup_btns[0]
    next_center = (btn_next.centerx, btn_next.centery)
    start_pos = cur_pos
    for s in range(1, 7):
        t = ease_in_out(s / 6)
        px = start_pos[0] + (next_center[0] - start_pos[0]) * t
        py = start_pos[1] + (next_center[1] - start_pos[1]) * t
        cur_pos = (px, py)
        capture_board(cur_pos, show_popup=True, win_line_points=(ext_start, ext_end))

    for _ in range(20):
        capture_board(cur_pos, show_popup=True, win_line_points=(ext_start, ext_end))

    print(f"Total showcase frames: {len(frames)}")

    showcase_gif = os.path.join(workspace_dir, "tictactoe_full_showcase.gif")
    frames[0].save(
        showcase_gif,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=70,
        loop=0
    )
    print(f"Saved: {showcase_gif} ({os.path.getsize(showcase_gif)/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    generate_gameplay_gif()
    generate_full_showcase_gif()
