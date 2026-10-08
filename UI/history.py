import pygame
from constants import *
from utils import draw_panel


class HistoryDrawer:
    """Sliding drawer for match history — hidden by default, toggle with a tab."""

    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.width = 340
        self.target_x = float(sw)     # offscreen
        self.current_x = float(sw)
        self.is_open = False
        self.logs = []
        self.scroll_y = 0

    def resize(self, sw, sh):
        self.sw, self.sh = sw, sh
        if not self.is_open:
            self.target_x = float(sw)
            self.current_x = float(sw)
        else:
            self.target_x = float(sw - self.width)

    def toggle(self):
        self.is_open = not self.is_open
        self.target_x = float(self.sw - self.width) if self.is_open else float(self.sw)

    def handle_scroll(self, dy):
        if not self.is_open:
            return
        self.scroll_y -= dy * 30
        max_scroll = max(0, len(self.logs) * 46 - (self.sh - TITLEBAR_H - 90))
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def add_log(self, winner, mode):
        n = len(self.logs) + 1
        if winner == 1:
            r = "X Won"
        elif winner == 2:
            r = "AI Won" if mode == "ai" else "O Won"
        else:
            r = "Draw"
        vs = "vs AI" if mode == "ai" else "vs Player"
        self.logs.append(f"#{n}  {vs}  —  {r}")

    def tab_rect(self):
        x = int(self.current_x) - 32
        y = self.sh // 2 - 55
        return pygame.Rect(x, y, 32, 110)

    def handle_click(self, pos):
        if self.tab_rect().collidepoint(pos):
            self.toggle()
            return True
        return False

    def update(self):
        diff = self.target_x - self.current_x
        self.current_x += diff * 0.14

    def draw(self, screen):
        self.update()
        m = pygame.mouse.get_pos()

        # Tab
        tab = self.tab_rect()
        tc = BTN_HOVER if tab.collidepoint(m) else FRAME_COLOR
        pygame.draw.rect(screen, tc, tab,
                         border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, FRAME_EDGE, tab, width=2,
                         border_top_left_radius=8, border_bottom_left_radius=8)
        arrow = FONT_SMALL.render("<<" if not self.is_open else ">>", True, BTN_TEXT)
        screen.blit(arrow, (tab.centerx - arrow.get_width() // 2,
                            tab.centery - arrow.get_height() // 2))

        # Drawer body
        cx = int(self.current_x)
        if cx >= self.sw - 1:
            return

        body = pygame.Rect(cx, TITLEBAR_H, self.width, self.sh - TITLEBAR_H)
        draw_panel(screen, body, DRAWER_BG, FRAME_EDGE, radius=0, border_w=0, shadow=False)
        pygame.draw.line(screen, FRAME_EDGE, (cx, TITLEBAR_H), (cx, self.sh), 3)

        # Header
        hdr = FONT_HEADING.render("History", True, TEXT_CREAM)
        screen.blit(hdr, (cx + 20, TITLEBAR_H + 18))
        pygame.draw.line(screen, CELL_COLOR, (cx + 20, TITLEBAR_H + 60),
                         (cx + self.width - 20, TITLEBAR_H + 60), 1)

        # Log entries
        y_start = TITLEBAR_H + 75
        h_area = self.sh - y_start - 20
        
        # Max scroll update just to be safe
        max_scroll = max(0, len(self.logs) * 46 - h_area)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))
        
        clip_rect = pygame.Rect(cx, y_start, self.width, h_area)
        screen.set_clip(clip_rect)
        
        y = y_start - self.scroll_y
        for entry in self.logs:
            if y + 46 > y_start and y < y_start + h_area:
                card = pygame.Rect(cx + 14, y, self.width - 28, 38)
                draw_panel(screen, card, DRAWER_CARD, FRAME_COLOR, radius=8, border_w=1, shadow=False)
                txt = FONT_SMALL.render(entry, True, TEXT_BROWN)
                screen.blit(txt, (cx + 26, y + 9))
            y += 46
            
        screen.set_clip(None)
