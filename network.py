import torch
import torch.nn as nn


class TicTacToeNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(9, 64), #9 is moves,64 is parameters for  hidden neural network nueron ----Input layer
            nn.ReLU(),

            nn.Linear(64, 64), #64  transforemed parametrs to 64 learned parametrs----Hidden layer
            nn.ReLU(),

            nn.Linear(64, 9)#64 learned parametrs to 9 best moves-----Output layer
        )

    def forward(self, state):
        return self.network(state)


if __name__ == "__main__":
    network = TicTacToeNetwork()

    state = torch.tensor(
        [1, 0, 2,
         0, 1, 0,
         2, 0, 0],
        dtype=torch.float32
    )

    output = network(state)

    print("Input:", state)
    print("Output:", output)
    print("Output shape:", output.shape)