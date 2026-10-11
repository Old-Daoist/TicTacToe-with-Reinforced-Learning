import pygame
from constants import (
    TITLEBAR_H, FRAME_COLOR, FRAME_EDGE, CELL_COLOR,
    BTN_COLOR, BTN_HOVER, BTN_TEXT, TEXT_BROWN, TEXT_CREAM,
    DRAWER_BG, DRAWER_CARD, FONT_HEADING, FONT_SMALL
)
from utils import draw_panel
from history_data import MatchHistory


class HistoryDrawer:
    """Sliding drawer UI for match history overlay."""

    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.width = 340
        self.target_x = float(sw)
        self.current_x = float(sw)
        self.is_open = False
        self.history = MatchHistory()
        self.scroll_y = 0

    @property
    def logs(self):
        return self.history.logs

    def add_log(self, winner, mode):
        self.history.add_match(winner, mode)

    def resize(self, sw, sh):
        self.sw, self.sh = sw, sh
        if not self.is_open:
            self.target_x = float(sw)
            self.current_x = float(sw)
        else:
            self.target_x = float(sw - self.width)
            self.current_x = float(sw - self.width)

    def open(self):
        self.is_open = True
        self.target_x = float(self.sw - self.width)

    def close(self):
        self.is_open = False
        self.target_x = float(self.sw)

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def handle_scroll(self, dy):
        if not self.is_open:
            return
        self.scroll_y -= dy * 30
        h_area = self.sh - TITLEBAR_H - 95
        max_scroll = max(0, len(self.history) * 46 - h_area)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def tab_rect(self):
        x = int(self.current_x) - 32
        y = self.sh // 2 - 55
        return pygame.Rect(x, y, 32, 110)

    def drawer_rect(self):
        cx = int(min(self.current_x, self.sw - self.width))
        return pygame.Rect(cx, 0, self.sw - cx, self.sh)

    def handle_click(self, pos):
        # 1. Click on tab handle
        if self.tab_rect().collidepoint(pos):
            self.toggle()
            return True

        # 2. When open: click inside consumes event, click outside closes drawer
        if self.is_open:
            if self.drawer_rect().collidepoint(pos):
                return True
            else:
                self.close()
                return True

        return False

    def update(self):
        diff = self.target_x - self.current_x
        self.current_x += diff * 0.14

    def draw(self, screen):
        self.update()
        m = pygame.mouse.get_pos()

        # Dimmed backdrop
        if self.current_x < self.sw:
            open_ratio = max(0.0, min(1.0, (self.sw - self.current_x) / self.width))
            if open_ratio > 0.01:
                dim = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
                dim.fill((0, 0, 0, int(65 * open_ratio)))
                screen.blit(dim, (0, 0))

        # Drawer body
        cx = int(self.current_x)
        if cx < self.sw - 1:
            body = pygame.Rect(cx, TITLEBAR_H, self.sw - cx, self.sh - TITLEBAR_H)
            draw_panel(screen, body, DRAWER_BG, FRAME_EDGE, radius=0, border_w=0, shadow=False)
            pygame.draw.line(screen, FRAME_EDGE, (cx, TITLEBAR_H), (cx, self.sh), 3)

            # Header
            hdr = FONT_HEADING.render("History", True, TEXT_CREAM)
            screen.blit(hdr, (cx + 20, TITLEBAR_H + 18))
            pygame.draw.line(screen, CELL_COLOR, (cx + 20, TITLEBAR_H + 60),
                             (cx + self.width - 20, TITLEBAR_H + 60), 1)

            # Scrollable log entries
            y_start = TITLEBAR_H + 75
            h_area = self.sh - y_start - 20
            max_scroll = max(0, len(self.history) * 46 - h_area)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

            clip_rect = pygame.Rect(cx, y_start, self.width, h_area)
            screen.set_clip(clip_rect)

            y = y_start - self.scroll_y
            if not self.history:
                empty_txt = FONT_SMALL.render("No matches played yet", True, (160, 130, 100))
                screen.blit(empty_txt, (cx + 26, y_start + 20))
            else:
                for entry in self.history:
                    if y + 46 > y_start and y < y_start + h_area:
                        card = pygame.Rect(cx + 14, y, self.width - 28, 38)
                        draw_panel(screen, card, DRAWER_CARD, FRAME_COLOR, radius=8, border_w=1, shadow=False)
                        txt = FONT_SMALL.render(entry, True, TEXT_BROWN)
                        screen.blit(txt, (cx + 26, y + 9))
                    y += 46

            screen.set_clip(None)

        # Tab button
        tab = self.tab_rect()
        tc = BTN_HOVER if tab.collidepoint(m) else FRAME_COLOR
        pygame.draw.rect(screen, tc, tab, border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, FRAME_EDGE, tab, width=2, border_top_left_radius=8, border_bottom_left_radius=8)
        arrow = FONT_SMALL.render("<<" if not self.is_open else ">>", True, BTN_TEXT)
        screen.blit(arrow, (tab.centerx - arrow.get_width() // 2, tab.centery - arrow.get_height() // 2))
