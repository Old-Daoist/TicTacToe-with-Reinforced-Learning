import torch
import torch.nn as nn
import json
import os

class TicTacToeNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        # Let's load the configuration from the config.json file!
        # This is super cool because we can change the size of the brain without changing this file.
        hidden_neurons = 64 # Default just in case
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                hidden_neurons = config.get("HIDDEN_NEURONS", 64)

        # Here we build our Neural Network. It's like a brain for the game!
        # It takes 9 inputs (for the 9 squares of the board)
        # It passes them through hidden layers to think.
        # And finally outputs 9 values (one for each possible move!)
        self.network = nn.Sequential(
            nn.Linear(9, hidden_neurons), # First layer takes 9 inputs and makes it bigger!
            nn.ReLU(),                    # Activation function (makes it learn non-linear things)

            nn.Linear(hidden_neurons, hidden_neurons), # Second layer, more thinking!
            nn.ReLU(),                    # Another activation

            nn.Linear(hidden_neurons, 9)  # Final layer outputs the 9 choices.
        )

    def forward(self, state):
        # This function runs when we pass a state into the network.
        # Like: output = network(state)
        return self.network(state)


if __name__ == "__main__":
    # This is just a test block to see if our network works.
    network = TicTacToeNetwork()

    # Let's create a fake board state! 1 = X, 2 = O, 0 = empty.
    state = torch.tensor(
        [1, 0, 2,
         0, 1, 0,
         2, 0, 0],
        dtype=torch.float32
    )

    # Pass the fake board into our brain
    output = network(state)

    print("Input:", state)
    print("Output (Q-values for each move):", output)
    print("Output shape:", output.shape)