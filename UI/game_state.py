WINNING_COMBOS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]


class GameState:
    """Pure game state and rules for 3x3 Tic-Tac-Toe."""

    def __init__(self, mode, p1_name, p2_name, p1_piece):
        self.mode = mode
        self.p1_name = p1_name.strip() if p1_name.strip() else "Player 1"
        self.p2_name = p2_name.strip() if p2_name.strip() else ("AI" if mode == "ai" else "Player 2")
        self.p1_piece = p1_piece

        if p1_piece == "X":
            self.x_name, self.o_name = self.p1_name, self.p2_name
            self.ai_piece = 2
        else:
            self.x_name, self.o_name = self.p2_name, self.p1_name
            self.ai_piece = 1

        self.board = [0] * 9
        self.current_player = 1
        self.game_over = False
        self.game_over_time = 0
        self.winner = 0
        self.win_cells = []
        self.scores = {"X": 0, "O": 0, "D": 0}

    def check_winner(self):
        for a, b, c in WINNING_COMBOS:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a], [a, b, c]
        return 0, []

    def make_move(self, idx, ticks=0):
        """Places current_player piece at idx. Returns (success, outcome) where outcome is winner or None."""
        if not (0 <= idx < 9) or self.board[idx] != 0 or self.game_over:
            return False, None

        self.board[idx] = self.current_player
        w, cells = self.check_winner()
        if w:
            self.game_over = True
            self.winner = w
            self.game_over_time = ticks
            self.win_cells = cells
            self.scores["X" if w == 1 else "O"] += 1
            return True, w
        elif 0 not in self.board:
            self.game_over = True
            self.winner = 0
            self.game_over_time = ticks
            self.win_cells = []
            self.scores["D"] += 1
            return True, 0
        else:
            self.current_player = 2 if self.current_player == 1 else 1
            return True, None

    def reset(self):
        next_first = self.winner if self.winner != 0 else 1
        self.board = [0] * 9
        self.current_player = next_first
        self.game_over = False
        self.game_over_time = 0
        self.winner = 0
        self.win_cells = []
        return next_first
