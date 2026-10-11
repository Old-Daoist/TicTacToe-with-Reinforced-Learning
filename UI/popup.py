import pygame
from constants import (
    FRAME_COLOR, FRAME_EDGE, CELL_COLOR, TEXT_BROWN, TEXT_CREAM,
    FONT_HEADING, FONT_BODY
)
from utils import draw_panel, draw_button


class VictoryPopup:
    """Beautiful victory / draw modal popup overlay shown after game ends."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self._icon_cache = {}

    def resize(self, w, h):
        self.w, self.h = w, h

    def get_buttons(self):
        """Returns the rects for (Next, Menu, Exit) buttons."""
        pw, ph = 480, 340
        py = self.h // 2 - ph // 2
        btn_w, btn_h = 130, 45
        gap = 15

        bx2 = self.w // 2 - btn_w // 2
        bx1 = bx2 - btn_w - gap
        bx3 = bx2 + btn_w + gap

        y = py + ph - 80
        return (
            pygame.Rect(bx1, y, btn_w, btn_h),
            pygame.Rect(bx2, y, btn_w, btn_h),
            pygame.Rect(bx3, y, btn_w, btn_h)
        )

    def handle_click(self, pos):
        """Checks click on popup buttons and returns 'next', 'menu', 'exit', or None."""
        btn_next, btn_menu, btn_exit = self.get_buttons()
        if btn_next.collidepoint(pos):
            return "next"
        elif btn_menu.collidepoint(pos):
            return "menu"
        elif btn_exit.collidepoint(pos):
            return "exit"
        return None

    def _get_icon(self, is_win):
        if is_win in self._icon_cache:
            return self._icon_cache[is_win]

        emoji_char = "🏆" if is_win else "🤝"
        icon_surf = None

        # Cross-platform emoji font matching
        for font_name in ["notocoloremoji", "segoeuiemoji", "applecoloremoji", "notoemoji", "symbola", "twemoji"]:
            path = pygame.font.match_font(font_name)
            if path:
                try:
                    f = pygame.font.Font(path, 64)
                    surf = f.render(emoji_char, True, TEXT_BROWN)
                    if surf.get_width() >= 32 and surf.get_height() >= 32:
                        target_h = 60
                        target_w = int(surf.get_width() * (target_h / surf.get_height()))
                        icon_surf = pygame.transform.smoothscale(surf, (target_w, target_h))
                        break
                except Exception:
                    pass

        # Vector fallback if emoji font is unavailable
        if icon_surf is None:
            icon_surf = pygame.Surface((64, 60), pygame.SRCALPHA)
            if is_win:
                gold = (212, 175, 55)
                dark_gold = (160, 120, 30)
                pygame.draw.polygon(icon_surf, gold, [(16, 8), (48, 8), (42, 34), (22, 34)])
                pygame.draw.polygon(icon_surf, dark_gold, [(16, 8), (48, 8), (42, 34), (22, 34)], 2)
                pygame.draw.arc(icon_surf, gold, pygame.Rect(8, 12, 16, 16), 1.5, 4.5, 3)
                pygame.draw.arc(icon_surf, gold, pygame.Rect(40, 12, 16, 16), 4.7, 1.7, 3)
                pygame.draw.rect(icon_surf, dark_gold, pygame.Rect(30, 34, 4, 12))
                pygame.draw.rect(icon_surf, gold, pygame.Rect(20, 46, 24, 8), border_radius=2)
            else:
                brown = (140, 90, 40)
                pygame.draw.circle(icon_surf, brown, (24, 28), 10, 3)
                pygame.draw.circle(icon_surf, brown, (40, 28), 10, 3)
                pygame.draw.line(icon_surf, brown, (16, 44), (48, 44), 4)

        self._icon_cache[is_win] = icon_surf
        return icon_surf

    def draw(self, screen, winner, x_name, o_name, scores):
        """Draws the modal overlay and victory card."""
        # Dim background
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Modal panel
        pw, ph = 480, 340
        px = self.w // 2 - pw // 2
        py = self.h // 2 - ph // 2
        popup_rect = pygame.Rect(px, py, pw, ph)

        draw_panel(screen, popup_rect, FRAME_COLOR, FRAME_EDGE, radius=22, border_w=4)
        inner = pygame.Rect(px + 10, py + 10, pw - 20, ph - 20)
        draw_panel(screen, inner, CELL_COLOR, FRAME_COLOR, radius=18, border_w=2, shadow=False)

        # Icon
        is_win = (winner in (1, 2))
        trophy = self._get_icon(is_win)
        screen.blit(trophy, (self.w // 2 - trophy.get_width() // 2, py + 30))

        # Title
        if winner == 1:
            title = f"{x_name} Wins!"
        elif winner == 2:
            title = f"{o_name} Wins!"
        else:
            title = "It's a Draw!"

        title_surf = FONT_HEADING.render(title, True, TEXT_BROWN)
        screen.blit(title_surf, (self.w // 2 - title_surf.get_width() // 2, py + 115))

        # Divider
        pygame.draw.line(screen, FRAME_COLOR, (px + 40, py + 165), (px + pw - 40, py + 165), 2)

        # Scores summary
        score_lines = [
            f"Player X:  {scores['X']}",
            f"Player O:  {scores['O']}",
            f"Draws:       {scores['D']}"
        ]
        y_off = py + 180
        for line in score_lines:
            s = FONT_BODY.render(line, True, TEXT_BROWN)
            screen.blit(s, (self.w // 2 - s.get_width() // 2, y_off))
            y_off += 28

        # Buttons
        m = pygame.mouse.get_pos()
        btn_next, btn_menu, btn_exit = self.get_buttons()
        draw_button(screen, btn_next, "Next Game", FONT_BODY, btn_next.collidepoint(m))
        draw_button(screen, btn_menu, "Main Menu", FONT_BODY, btn_menu.collidepoint(m))
        draw_button(screen, btn_exit, "Exit", FONT_BODY, btn_exit.collidepoint(m))
