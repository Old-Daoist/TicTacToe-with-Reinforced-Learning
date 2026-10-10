import random

from game import TicTacToe


class TicTacToeEnv:
    def __init__(self):
        self.game = TicTacToe()

    def reset(self):
        self.game.reset()
        return self.observation()

    # def observation(self):
    #     return [1 if x == 1 else -1 if x == 2 else 0 for x in self.game.board]

    # we want whoever's turn it currently is (self.game.current_player) to always see themselves as +1, and the opponent as -1
    def observation(self):
        cur = self.game.current_player
        opp = 2 if cur == 1 else 1
        return [1 if x == cur else -1 if x == opp else 0 for x in self.game.board]


    def legal_actions(self):
        return self.game.legal_actions()

    def step(self, action):
        # 1. Check if the chosen move is legal
        if action not in self.game.legal_actions():
            return self.observation(), -1, True

        # 2. Remember who is taking this move before the turn switches
        player_who_moved = self.game.current_player
        
        # 3. Make the move (this automatically updates the board and switches current_player)
        self.game.make_move(action)
        
        # 4. Check if this move won the game
        if self.game.check_winner() == player_who_moved:
            return self.observation(), 1, True
        
        # 5. Check if it's a draw
        if self.game.is_draw():
            return self.observation(), 0.5, True
        
        # 6. Game continues -> next player's turn (reward 0, not done)
        return self.observation(), 0, False

    # def opponent_move(self):
    #     legal_actions = self.legal_actions()

    #     if not legal_actions:
    #         return

    #     action = random.choice(legal_actions)
    #     self.game.make_move(action)


if __name__ == "__main__":
    env = TicTacToeEnv()

    print("Initial:", env.reset())
    print("Legal actions:", env.legal_actions())

    state, reward, done = env.step(4)

    print("After AI action + opponent:", state)
    print("Legal actions:", env.legal_actions())
    print("Reward:", reward)
    print("Done:", done)