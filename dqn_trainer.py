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
            "EPSILON_END": 0.05,
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

    # Time to do the learning! Backpropagation updates the weights in our brain.
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
    total_rewards_list = []
    wins = 0
    losses = 0
    draws = 0
    
    print(f"Starting training for {episodes} episodes...")

    # LOOP THROUGH EACH GAME (EPISODE)
    for episode in range(1, episodes + 1):

        # Start a brand new game
        state = env.reset()

        total_reward = 0
        loss = None

        while True:
            # What moves are we allowed to make right now?
            legal_actions = env.legal_actions()

            # Choose an action! Sometimes we explore (random), sometimes we exploit (use brain)
            # This is called epsilon-greedy!
            action = select_action(
                network,
                state,
                legal_actions,
                epsilon
            )

            # Do the action in the game and see what happens!
            next_state, reward, done = env.step(action)

            # Save what just happened into our memory bank
            buffer.add(
                state,
                action,
                reward,
                next_state,
                done
            )

            # Learn from our memories!
            loss = train_step(
                network,
                target_network,
                optimizer,
                buffer,
                batch_size,
                gamma
            )

            # Update our current state for the next turn
            state = next_state
            total_reward += reward

            # If the game is over, break out of this loop!
            if done:
                if reward == 1:
                    wins += 1
                elif reward == -1:
                    losses += 1
                else:
                    draws += 1
                break
        
        # Every once in a while, copy the main brain over to the target brain
        if episode % target_update_freq == 0:
            target_network.load_state_dict(network.state_dict())

        # Slowly stop exploring randomly over time, and use the brain more!
        epsilon = max(
            epsilon_end,
            epsilon * epsilon_decay
        )

        total_rewards_list.append(total_reward)

        # Print our progress so we can watch it learn!
        if episode % 100 == 0:
            print(
                f"Episode: {episode}, "
                f"Reward: {total_reward}, "
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
    
    with open(result_filepath, "w") as f:
        f.write("--- TIC-TAC-TOE TRAINING RESULTS ---\n\n")
        f.write("1. HYPER-PARAMETERS USED:\n")
        for key, value in config.items():
            f.write(f"   {key}: {value}\n")
        
        f.write("\n2. TRAINING SUMMARY:\n")
        f.write(f"   Total Episodes: {episodes}\n")
        
        # Calculate average reward over the last 100 games
        recent_avg = sum(total_rewards_list[-100:]) / min(100, len(total_rewards_list))
        f.write(f"   Average Reward (Last 100 Episodes): {recent_avg:.2f}\n")
        
        # Calculate win/loss/draw rates (Accuracy)
        win_rate = (wins / episodes) * 100
        loss_rate = (losses / episodes) * 100
        draw_rate = (draws / episodes) * 100
        non_loss_rate = ((wins + draws) / episodes) * 100
        
        f.write(f"   Win Rate: {win_rate:.2f}%\n")
        f.write(f"   Loss Rate: {loss_rate:.2f}%\n")
        f.write(f"   Draw Rate: {draw_rate:.2f}%\n")
        f.write(f"   Overall Accuracy (Win + Draw): {non_loss_rate:.2f}%\n")
        f.write("\nLook at you! You're a machine learning expert now! 😎\n")

    print(f"Training results saved to: {result_filepath}")


if __name__ == "__main__":
    train()