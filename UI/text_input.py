import pygame
from constants import (
    FRAME_COLOR, FRAME_EDGE, CELL_COLOR, TEXT_BROWN, TEXT_CREAM, FONT_PIECE
)
from utils import draw_panel


def get_clipboard_text():
    """Safely retrieves string from system clipboard."""
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        data = pygame.scrap.get(pygame.SCRAP_TEXT)
        if data:
            if isinstance(data, bytes):
                return data.decode("utf-8", errors="ignore").replace("\x00", "")
            return str(data)
    except Exception:
        pass
    return ""


def set_clipboard_text(text):
    """Safely writes string to system clipboard."""
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
    except Exception:
        pass


class TextInputBox:
    """Interactive text box with selection highlight, cursor navigation,
    Ctrl+A (Select All), Backspace/Delete removal, double-click selection,
    clear button ('×'), and Tab focus support."""

    def __init__(self, default_text="", placeholder="Enter name...", max_len=14):
        self.text = default_text
        self.placeholder = placeholder
        self.max_len = max_len
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.active = False

        self.cursor = len(default_text)
        self.sel_start = 0
        self.sel_end = len(default_text)
        self.drag_anchor = None
        self.is_dragging = False
        self.last_click_time = 0
        self.last_click_pos = (0, 0)

    def set_rect(self, rect):
        self.rect = rect

    def set_text(self, text):
        self.text = str(text)[:self.max_len]
        self.cursor = len(self.text)
        self.clear_selection()

    def select_all(self):
        self.sel_start = 0
        self.sel_end = len(self.text)
        self.cursor = len(self.text)
        self.drag_anchor = None

    def clear_selection(self):
        self.sel_start = self.cursor
        self.sel_end = self.cursor
        self.drag_anchor = None

    def has_selection(self):
        return self.sel_start != self.sel_end

    def get_selection_bounds(self):
        return min(self.sel_start, self.sel_end), max(self.sel_start, self.sel_end)

    def get_selected_text(self):
        s_min, s_max = self.get_selection_bounds()
        return self.text[s_min:s_max]

    def delete_selection(self):
        if not self.has_selection():
            return False
        s_min, s_max = self.get_selection_bounds()
        self.text = self.text[:s_min] + self.text[s_max:]
        self.cursor = s_min
        self.clear_selection()
        return True

    def delete_all(self):
        self.text = ""
        self.cursor = 0
        self.clear_selection()

    def insert_text(self, new_chars):
        if self.has_selection():
            self.delete_selection()
        avail = self.max_len - len(self.text)
        if avail > 0:
            add = new_chars[:avail]
            self.text = self.text[:self.cursor] + add + self.text[self.cursor:]
            self.cursor += len(add)
            self.clear_selection()

    def clear_btn_rect(self):
        size = 20
        return pygame.Rect(self.rect.right - 28, self.rect.centery - size // 2, size, size)

    def get_char_index_at_x(self, x, font):
        text_x = self.rect.x + 12
        if x <= text_x or not self.text:
            return 0
        for i in range(1, len(self.text) + 1):
            sub_w = font.size(self.text[:i])[0]
            prev_w = font.size(self.text[:i - 1])[0] if i > 1 else 0
            mid = (prev_w + sub_w) / 2
            if x <= text_x + mid:
                return i - 1
            if x <= text_x + sub_w:
                return i
        return len(self.text)

    def handle_mouse_down(self, pos, font):
        if self.active and len(self.text) > 0 and self.clear_btn_rect().collidepoint(pos):
            self.delete_all()
            return "clear"

        if self.rect.collidepoint(pos):
            now = pygame.time.get_ticks()
            if (now - self.last_click_time < 350 and
                abs(pos[0] - self.last_click_pos[0]) < 15 and
                abs(pos[1] - self.last_click_pos[1]) < 15):
                # Double click selects all
                self.select_all()
                self.is_dragging = False
            else:
                idx = self.get_char_index_at_x(pos[0], font)
                self.cursor = idx
                self.clear_selection()
                self.drag_anchor = idx
                self.is_dragging = True
            self.last_click_time = now
            self.last_click_pos = pos
            self.active = True
            return "focus"
        else:
            self.active = False
            self.clear_selection()
            self.is_dragging = False
            return None

    def handle_mouse_motion(self, pos, font):
        if self.is_dragging and self.active and self.drag_anchor is not None:
            idx = self.get_char_index_at_x(pos[0], font)
            self.cursor = idx
            self.sel_start = self.drag_anchor
            self.sel_end = idx

    def handle_mouse_up(self):
        self.is_dragging = False

    def handle_key_down(self, ev):
        if not self.active:
            return None

        is_ctrl = bool((ev.mod & pygame.KMOD_CTRL) or (ev.mod & pygame.KMOD_GUI))
        is_shift = bool(ev.mod & pygame.KMOD_SHIFT)

        # 1. Select All (Ctrl+A / Cmd+A)
        if is_ctrl and ev.key == pygame.K_a:
            self.select_all()
            return "handled"

        # 2. Copy (Ctrl+C / Cmd+C)
        if is_ctrl and ev.key == pygame.K_c:
            txt = self.get_selected_text() if self.has_selection() else self.text
            if txt:
                set_clipboard_text(txt)
            return "handled"

        # 3. Cut (Ctrl+X / Cmd+X)
        if is_ctrl and ev.key == pygame.K_x:
            txt = self.get_selected_text() if self.has_selection() else self.text
            if txt:
                set_clipboard_text(txt)
            if self.has_selection():
                self.delete_selection()
            else:
                self.delete_all()
            return "handled"

        # 4. Paste (Ctrl+V / Cmd+V)
        if is_ctrl and ev.key == pygame.K_v:
            clip = get_clipboard_text()
            if clip:
                clean_clip = "".join(c for c in clip.split("\n")[0] if c.isprintable() and c not in ("\t", "\r", "\n"))
                if clean_clip:
                    self.insert_text(clean_clip)
            return "handled"

        # 5. Backspace
        if ev.key == pygame.K_BACKSPACE:
            if self.has_selection():
                self.delete_selection()
            elif self.cursor > 0:
                self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                self.cursor -= 1
                self.clear_selection()
            return "handled"

        # 6. Delete
        if ev.key == pygame.K_DELETE:
            if self.has_selection():
                self.delete_selection()
            elif self.cursor < len(self.text):
                self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
                self.clear_selection()
            return "handled"

        # 7. Left Arrow
        if ev.key == pygame.K_LEFT:
            if is_shift:
                if not self.has_selection():
                    self.drag_anchor = self.cursor
                self.cursor = max(0, self.cursor - 1)
                self.sel_start = self.drag_anchor
                self.sel_end = self.cursor
            else:
                if self.has_selection():
                    self.cursor = min(self.sel_start, self.sel_end)
                    self.clear_selection()
                else:
                    self.cursor = max(0, self.cursor - 1)
                    self.clear_selection()
            return "handled"

        # 8. Right Arrow
        if ev.key == pygame.K_RIGHT:
            if is_shift:
                if not self.has_selection():
                    self.drag_anchor = self.cursor
                self.cursor = min(len(self.text), self.cursor + 1)
                self.sel_start = self.drag_anchor
                self.sel_end = self.cursor
            else:
                if self.has_selection():
                    self.cursor = max(self.sel_start, self.sel_end)
                    self.clear_selection()
                else:
                    self.cursor = min(len(self.text), self.cursor + 1)
                    self.clear_selection()
            return "handled"

        # 9. Home
        if ev.key == pygame.K_HOME:
            if is_shift:
                if not self.has_selection():
                    self.drag_anchor = self.cursor
                self.cursor = 0
                self.sel_start = self.drag_anchor
                self.sel_end = 0
            else:
                self.cursor = 0
                self.clear_selection()
            return "handled"

        # 10. End
        if ev.key == pygame.K_END:
            if is_shift:
                if not self.has_selection():
                    self.drag_anchor = self.cursor
                self.cursor = len(self.text)
                self.sel_start = self.drag_anchor
                self.sel_end = len(self.text)
            else:
                self.cursor = len(self.text)
                self.clear_selection()
            return "handled"

        # 11. Printable characters
        char = ev.unicode
        if char and char.isprintable() and char not in ("\t", "\r", "\n"):
            self.insert_text(char)
            return "handled"

        return None

    def draw(self, screen, font):
        m = pygame.mouse.get_pos()
        bc = FRAME_COLOR if self.active else FRAME_EDGE
        border_w = 3 if self.active else 2
        draw_panel(screen, self.rect, CELL_COLOR, bc, radius=8, border_w=border_w, shadow=False)

        right_margin = 32 if (self.active and len(self.text) > 0) else 14
        content_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 4,
                                   self.rect.width - 8 - right_margin, self.rect.height - 8)
        screen.set_clip(content_rect)

        tx = self.rect.x + 12
        ty = self.rect.centery - font.get_height() // 2

        if not self.text and not self.active:
            ph = font.render(self.placeholder, True, (155, 128, 95))
            screen.blit(ph, (tx, ty))
        elif self.active and self.has_selection():
            s_min, s_max = self.get_selection_bounds()
            s_before = self.text[:s_min]
            s_sel = self.text[s_min:s_max]
            s_after = self.text[s_max:]

            w_before = font.size(s_before)[0]
            w_sel = font.size(s_sel)[0]

            if s_before:
                txt_b = font.render(s_before, True, TEXT_BROWN)
                screen.blit(txt_b, (tx, ty))

            # Selection highlight rectangle
            sel_rect = pygame.Rect(tx + w_before, self.rect.y + 7, w_sel, self.rect.height - 14)
            pygame.draw.rect(screen, (75, 105, 140), sel_rect, border_radius=3)

            txt_s = font.render(s_sel, True, TEXT_CREAM)
            screen.blit(txt_s, (tx + w_before, ty))

            if s_after:
                txt_a = font.render(s_after, True, TEXT_BROWN)
                screen.blit(txt_a, (tx + w_before + w_sel, ty))
        else:
            if self.text:
                txt = font.render(self.text, True, TEXT_BROWN)
                screen.blit(txt, (tx, ty))

            if self.active:
                now = pygame.time.get_ticks()
                if (now // 500) % 2 == 0:
                    cx = tx + font.size(self.text[:self.cursor])[0]
                    cy1 = self.rect.centery - font.get_height() // 2 + 1
                    cy2 = self.rect.centery + font.get_height() // 2 - 1
                    pygame.draw.line(screen, FRAME_EDGE, (cx, cy1), (cx, cy2), 2)

        screen.set_clip(None)

        # Clear button ("×")
        if self.active and len(self.text) > 0:
            cbtn = self.clear_btn_rect()
            hovered = cbtn.collidepoint(m)
            bg_col = (185, 145, 105) if hovered else (205, 175, 135)
            pygame.draw.circle(screen, bg_col, cbtn.center, 9)
            pygame.draw.circle(screen, FRAME_EDGE, cbtn.center, 9, width=1)
            x_txt = FONT_PIECE.render("×", True, FRAME_EDGE if hovered else TEXT_BROWN)
            screen.blit(x_txt, (cbtn.centerx - x_txt.get_width() // 2,
                                cbtn.centery - x_txt.get_height() // 2 - 1))
