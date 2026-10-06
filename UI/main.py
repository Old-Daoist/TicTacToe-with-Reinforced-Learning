import pygame
import sys
from constants import *
from utils import create_bg, draw_panel
from menu import MainMenu, SetupMenu
from board import GameBoard
from history import HistoryDrawer


def main():
    pygame.init()

    w, h = DEFAULT_W, DEFAULT_H
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    # pygame.display.set_caption("Tic-Tac-Toe — Natural Edition")
    clock = pygame.time.Clock()
    is_fs = False

    bg = create_bg(w, h)
    history = HistoryDrawer(w, h)
    menu = MainMenu(w, h)
    setup = None
    board = None
    state = "MENU"  # MENU | SETUP | GAME

    def rebuild(nw, nh):
        nonlocal w, h, bg, menu, setup, history, board
        w, h = nw, nh
        bg = create_bg(w, h)
        menu.resize(w, h)
        if setup: setup.resize(w, h)
        history.resize(w, h)
        if board:
            board.resize(w, h)

    running = True
    while running:
        clock.tick(60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.VIDEORESIZE and not is_fs:
                screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                rebuild(ev.w, ev.h)

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if is_fs:
                        is_fs = False
                        screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H), pygame.RESIZABLE)
                        rebuild(DEFAULT_W, DEFAULT_H)
                    else:
                        running = False
                elif ev.key == pygame.K_F11:
                    is_fs = not is_fs
                    if is_fs:
                        info = pygame.display.Info()
                        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                        rebuild(info.current_w, info.current_h)
                    else:
                        screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H), pygame.RESIZABLE)
                        rebuild(DEFAULT_W, DEFAULT_H)
                elif state == "SETUP":
                    setup.handle_event(ev)

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = ev.pos

                if state == "GAME":
                    if history.handle_click(pos):
                        pass
                    else:
                        action = board.handle_click(pos)
                        if action == "back":
                            state = "MENU"
                elif state == "MENU":
                    action = menu.handle_click(pos)
                    if action in ("ai", "human"):
                        setup = SetupMenu(w, h, action)
                        state = "SETUP"
                elif state == "SETUP":
                    action = setup.handle_event(ev)
                    if action == "back":
                        state = "MENU"
                    elif action == "start":
                        board = GameBoard(w, h, setup.mode, setup.p1_name, setup.p2_name, setup.p1_piece, history)
                        state = "GAME"

        # ======== RENDER ========
        screen.blit(bg, (0, 0))

        # Page content
        if state == "MENU":
            menu.draw(screen)
        elif state == "SETUP":
            setup.draw(screen)
        elif state == "GAME":
            board.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
