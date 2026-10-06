import pygame
pygame.init()

# ============================================
# NATURAL WOODEN THEME — Professional Edition
# ============================================

# Window
DEFAULT_W, DEFAULT_H = 1280, 820

# ---- Color Palette ----
# Background
BG_DARK = (38, 50, 38)
BG_MEDIUM = (52, 68, 48)

# Wood tones
FRAME_COLOR = (78, 44, 24)        # Dark mahogany frame
FRAME_EDGE = (55, 30, 15)         # Even darker edge
CELL_COLOR = (200, 168, 120)      # Warm tan cell
CELL_HOVER = (215, 185, 140)      # Lighter on hover
CELL_WIN = (218, 190, 80)         # Golden winning cell

# Pieces
X_DARK = (90, 48, 22)             # Carved dark brown X
X_LIGHT = (115, 65, 32)           # Lighter X highlight
O_DARK = (75, 42, 18)             # Carved dark brown O
O_LIGHT = (100, 58, 28)           # Lighter O highlight

# UI chrome
BAR_COLOR = (62, 36, 18)
BAR_ACCENT = (48, 26, 12)
BTN_COLOR = (95, 60, 32)
BTN_HOVER = (120, 78, 42)
BTN_TEXT = (245, 235, 215)
TEXT_CREAM = (250, 240, 220)
TEXT_BROWN = (60, 32, 14)
GOLD = (210, 175, 55)
GOLD_LIGHT = (245, 220, 130)

# Drawer
DRAWER_BG = (65, 38, 20)
DRAWER_CARD = (180, 148, 105)

# ---- Fonts ----
try:
    FONT_TITLE = pygame.font.SysFont("georgia", 52, bold=True)
    FONT_HEADING = pygame.font.SysFont("georgia", 32, bold=True)
    FONT_BODY = pygame.font.SysFont("georgia", 22)
    FONT_SMALL = pygame.font.SysFont("georgia", 17)
    FONT_PIECE = pygame.font.SysFont("georgia", 14, bold=True)
except Exception:
    FONT_TITLE = pygame.font.Font(None, 60)
    FONT_HEADING = pygame.font.Font(None, 38)
    FONT_BODY = pygame.font.Font(None, 26)
    FONT_SMALL = pygame.font.Font(None, 20)
    FONT_PIECE = pygame.font.Font(None, 18)

# ---- Layout helper ----
TITLEBAR_H = 0
TOOLBAR_H = 52

def get_board_layout(w, h):
    """Returns (board_size, cell_size, board_x, board_y) perfectly centered."""
    area_top = TITLEBAR_H + TOOLBAR_H + 60   # space for status pill
    area_h = h - area_top - 30                # bottom margin
    area_w = w - 40                           # side margins
    board_size = int(min(area_w * 0.6, area_h * 0.92))
    board_size = board_size - (board_size % 3)  # make divisible by 3
    cell = board_size // 3
    bx = (w - board_size) // 2
    by = area_top + (area_h - board_size) // 2
    return board_size, cell, bx, by
