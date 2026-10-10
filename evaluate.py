import random

import torch

from environment import TicTacToeEnv
from network import TicTacToeNetwork


MODEL_PATH = "tictactoe_model.pth"
GAMES = 10000



def select_best_action(network, state, legal_actions):
    state = torch.tensor(state, dtype=torch.float32)

    with torch.no_grad():
        q_values = network(state)

    legal_q_values = q_values[legal_actions]

    best_index = torch.argmax(legal_q_values)

    return legal_actions[best_index.item()]


def play_game(network, ai_player=1):
    """
    Simulate a game where:
    - ai_player (1 or 2) is controlled by our trained neural network.
    - The opponent is controlled by random moves.
    Returns:
       1 if AI won
      -1 if Opponent won
       0 if Draw
    """
    env = TicTacToeEnv()
    state = env.reset()

    while True:
        current_player = env.game.current_player
        legal_actions = env.legal_actions()

        if current_player == ai_player:
            # AI chooses the best move
            action = select_best_action(network, state, legal_actions)
        else:
            # Opponent makes a random move
            action = random.choice(legal_actions)

        next_state, _, done = env.step(action)
        state = next_state

        if done:
            winner = env.game.check_winner()
            if winner == ai_player:
                return 1   # AI won
            elif winner == 0:
                return 0   # Draw
            else:
                return -1  # AI lost


def evaluate():
    network = TicTacToeNetwork()
    network.load_state_dict(
        torch.load(
            MODEL_PATH,
            weights_only=True
        )
    )
    network.eval()

    for role, name in [(1, "AI as X (Plays 1st)"), (2, "AI as O (Plays 2nd)")]:
        ai_wins = 0
        opp_wins = 0
        draws = 0

        for _ in range(GAMES):
            res = play_game(network, ai_player=role)
            if res == 1:
                ai_wins += 1
            elif res == -1:
                opp_wins += 1
            else:
                draws += 1

        print(f"\n--- {name} vs Random Opponent ({GAMES} Games) ---")
        print(f"AI Wins:  {ai_wins} ({ai_wins / GAMES * 100:.2f}%)")
        print(f"AI Losses: {opp_wins} ({opp_wins / GAMES * 100:.2f}%)")
        print(f"Draws:    {draws} ({draws / GAMES * 100:.2f}%)")


if __name__ == "__main__":
    evaluate()