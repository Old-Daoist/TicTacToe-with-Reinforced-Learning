import torch
import torch.nn as nn
import torch.optim as optim
import json
import os
import datetime

from environment import TicTacToeEnv
from network import TicTacToeNetwork
from replay_buffer import ReplayBuffer
from dqn import select_action

def load_config():
    """This function loads our hyper-parameters from the config.json file!"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        # Fallback default values if the file somehow goes missing
        return {
            "GAMMA": 0.99,
            "LEARNING_RATE": 0.001,
            "BUFFER_SIZE": 50000,
            "BATCH_SIZE": 128,
            "EPISODES": 100000,
            "TARGET_UPDATE_FREQ": 100,
            "EPSILON_START": 1.0,
            "EPSILON_END": 0.0000,
            "EPSILON_DECAY": 0.9999
        }

def train_step(network, target_network, optimizer, buffer, batch_size, gamma):
    """
    Here we take a batch of past experiences and learn from them!
    This is called 'experience replay'.
    """
    # If we don't have enough memories yet, we can't learn!
    if not buffer.can_sample(batch_size):
        return None

    # Get a random batch of memories from our replay buffer
    batch = buffer.sample(batch_size)

    states = []
    actions = []
    rewards = []
    next_states = []
    dones = []

    # Unpack all the memories into separate lists
    for state, action, reward, next_state, done in batch:
        states.append(state)
        actions.append(action)
        rewards.append(reward)
        next_states.append(next_state)
        dones.append(done)

    # Convert the lists into PyTorch tensors (which are like super-fast arrays for math)
    states = torch.tensor(states, dtype=torch.float32)
    actions = torch.tensor(actions, dtype=torch.long)
    rewards = torch.tensor(rewards, dtype=torch.float32)
    next_states = torch.tensor(next_states, dtype=torch.float32)
    dones = torch.tensor(dones, dtype=torch.float32)

    # What did our main network think the value of the action we took was?
    current_q_values = network(states).gather(
        1,
        actions.unsqueeze(1)
    ).squeeze(1)

    # Calculate what the value SHOULD have been (the target)
    with torch.no_grad():
        next_q_preds = target_network(next_states)
        
        # VERY IMPORTANT FIX: Mask out illegal actions!
        # If we don't do this, our AI might learn to do illegal moves!
        illegal_mask = (next_states != 0)
        next_q_preds[illegal_mask] = -1e9 # Make illegal moves look terribly bad!
        
        # What's the best possible move in the next state?
        next_q_values = next_q_preds.max(dim=1).values

        # Bellman Equation! Reward now + (discount factor * future reward)
        target_q_values = (
            rewards
            + gamma * next_q_values * (1 - dones)
        )

    # We want to make our current predictions closer to our target predictions!
    # MSELoss = Mean Squared Error Loss (calculates the difference)
    loss_function = nn.MSELoss()

    loss = loss_function(
        current_q_values,
        target_q_values
    )

    # Time to do the learning! Backpr opagation updates the weights in our brain.
    optimizer.zero_grad() # Clear old gradients
    loss.backward()       # Calculate new gradients
    optimizer.step()      # Update the weights!

    return loss.item()


def train():
    """This is the main function that runs the whole training process."""
    
    # Load all our parameters and settings from the config file
    config = load_config()
    gamma = config["GAMMA"]
    learning_rate = config["LEARNING_RATE"]
    buffer_size = config["BUFFER_SIZE"]
    batch_size = config["BATCH_SIZE"]
    episodes = config["EPISODES"]
    target_update_freq = config["TARGET_UPDATE_FREQ"]
    epsilon = config["EPSILON_START"]
    epsilon_end = config["EPSILON_END"]
    epsilon_decay = config["EPSILON_DECAY"]

    # Let's make sure our Data folder exists to save our results later
    data_dir = os.path.join(os.path.dirname(__file__), "Data")
    os.makedirs(data_dir, exist_ok=True)

    # 1. Create the game environment
    env = TicTacToeEnv()

    # 2. Create our Neural Networks (The brains)
    # We use a main network and a target network to make learning more stable!
    network = TicTacToeNetwork()
    target_network = TicTacToeNetwork()
    
    # Make the target network identical to the main network to start
    target_network.load_state_dict(network.state_dict())
    target_network.eval() # We only evaluate the target network, we don't train it directly

    # 3. Create the Optimizer (The teacher that tells the network how to change its weights)
    optimizer = optim.Adam(
        network.parameters(),
        lr=learning_rate
    )

    # 4. Create the Replay Buffer (The memory bank)
    buffer = ReplayBuffer(buffer_size)

    # Variables to track progress
    x_wins = 0
    o_wins = 0
    draws = 0

    
    print(f"Starting training for {episodes} episodes...")

    # LOOP THROUGH EACH GAME (EPISODE)
    for episode in range(1, episodes + 1):

        # Start a brand new game
        state = env.reset()
        
        # Record moves for both players during this game: {1: [(s, a), ...], 2: [(s, a), ...]}
        moves_by_player = {1: [], 2: []}
        loss = None
        
        while True:
            current_player = env.game.current_player
            legal_actions = env.legal_actions()
          
            # The network chooses a move for whichever player's turn it is!
            action = select_action(
                network,
                state,
                legal_actions,
                epsilon
            )
            
            # Record this player's state and action
            moves_by_player[current_player].append((state, action))
            
            # Execute the move
            next_state, _, done = env.step(action)
            state = next_state
            if done:
                winner = env.game.check_winner()
                if winner == 1:
                    x_wins += 1
                elif winner == 2:
                    o_wins += 1
                else:
                    draws += 1
                
                # Add experiences to the buffer for BOTH players
                for p in [1, 2]:
                    p_moves = moves_by_player[p]
                    if not p_moves:
                        continue
                    
                    # Decide final reward for player p
                    if winner == p:
                        outcome_reward = 1.0
                    elif winner == 0:
                        outcome_reward = 0.5  # Draw
                    else:
                        outcome_reward = -1.0  # Loss
                    
                    # Intermediate moves get reward 0.0, final move gets outcome_reward
                    for i in range(len(p_moves) - 1):
                        s, a = p_moves[i]
                        s_next, _ = p_moves[i + 1]
                        buffer.add(s, a, 0.0, s_next, False)
                    
                    # Last move for player p
                    s_last, a_last = p_moves[-1]
                    buffer.add(s_last, a_last, outcome_reward, [0] * 9, True)
                
                # Learn from memories in replay buffer
                loss = train_step(
                    network,
                    target_network,
                    optimizer,
                    buffer,
                    batch_size,
                    gamma
                )
                break
        
        # Every once in a while, copy the main brain over to the target brain
        if episode % target_update_freq == 0:
            target_network.load_state_dict(network.state_dict())

        # Slowly stop exploring randomly over time, and use the brain more!
        epsilon = max(
            epsilon_end,
            epsilon * epsilon_decay
        )


        # Print our progress so we can watch it learn!
        if episode % 100 == 0:
            print(
                f"Episode: {episode}, "
                f"X Wins: {x_wins}, "
                f"O Wins: {o_wins}, "
                f"Draws: {draws}, "
                f"Epsilon: {epsilon:.3f}, "
                f"Loss: {loss}"
            )


    # YAY! Training is all done. Time to save our work!
    # Save the trained brain (model)
    torch.save(
        network.state_dict(),
        "tictactoe_model.pth"
    )

    print("Training complete.")
    print("Model saved as tictactoe_model.pth")
    
    # Save the results of this training run into the Data folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"training_result_{timestamp}.txt"
    result_filepath = os.path.join(data_dir, result_filename)
    
    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write("--- TIC-TAC-TOE TRAINING RESULTS ---\n\n")
        f.write("1. HYPER-PARAMETERS USED:\n")
        for key, value in config.items():
            f.write(f"   {key}: {value}\n")
        
        f.write("\n2. TRAINING SUMMARY:\n")
        f.write(f"   Total Episodes: {episodes}\n")
        
        # Calculate win and draw rates for Self-Play
        x_win_rate = (x_wins / episodes) * 100
        o_win_rate = (o_wins / episodes) * 100
        draw_rate = (draws / episodes) * 100
        
        f.write(f"   X Win Rate: {x_win_rate:.2f}%\n")
        f.write(f"   O Win Rate: {o_win_rate:.2f}%\n")
        f.write(f"   Draw Rate: {draw_rate:.2f}%\n")


    print(f"Training results saved to: {result_filepath}")


if __name__ == "__main__":
    train()