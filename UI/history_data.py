class MatchHistory:
    """Manages match records and formatted log strings."""

    def __init__(self):
        self.logs = []

    def add_match(self, winner, mode):
        """Adds a new match result entry."""
        n = len(self.logs) + 1
        if winner == 1:
            r = "X Won"
        elif winner == 2:
            r = "AI Won" if mode == "ai" else "O Won"
        else:
            r = "Draw"
        vs = "vs AI" if mode == "ai" else "vs Player"
        self.logs.append(f"#{n}  {vs}  —  {r}")

    def clear(self):
        self.logs.clear()

    def count(self):
        return len(self.logs)

    def __iter__(self):
        return iter(self.logs)

    def __len__(self):
        return len(self.logs)
