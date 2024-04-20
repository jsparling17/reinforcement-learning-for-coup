import numpy as np
import gymnasium as gym
import random
import math
import matplotlib
import matplotlib.pyplot as plt
from collections import deque
from itertools import count
from argparse import ArgumentParser

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from agent import Transition, ReplayBuffer, DQN
from coup.coup import Coup
from coup.player import GreedyPlayer, HeuristicPlayer, RandomPlayer


class Trainer:
    """A class used to train the Deep Q Learning network for coup."""

    # BATCH_SIZE is the number of transitions sampled from the replay buffer
    # GAMMA is the discount factor
    # EPS_START is the starting value of epsilon
    # EPS_END is the final value of epsilon
    # EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
    # TAU is the update rate of the target network
    # LR is the learning rate of the AdamW optimizer
    # STATE_SIZE is the dimension of the input vector representing the state of the game
    # ACTION_COUNT is the dimension of the output vector representing actions

    def __init__(self, env: Coup, BATCH_SIZE: int = 128,
                 GAMMA: float = 0.99, EPS_START: float = 0.9, 
                 EPS_END: float = 0.05, EPS_DECAY: float = 1000,
                 TAU: float = 0.005, LR: float = 1e-4):
        
        self.env: Coup = env
        self.state_size: int = env.observation_space.shape[0]
        self.action_count: int = env.action_space.shape[0]
        
        self.batch_size: int = BATCH_SIZE
        self.gamma: float = GAMMA
        self.eps_start: float = EPS_START
        self.eps_end: float = EPS_END
        self.eps_decay: float = EPS_DECAY
        self.tau: float = TAU
        self.lr: float = LR

        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        self.policy_net: DQN = DQN(self.state_size, self.action_count).to(self.device)
        self.target_net: DQN = DQN(self.state_size, self.action_count).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=LR, amsgrad=True)
        self.memory: ReplayBuffer = ReplayBuffer(10000)

        self.steps_done: int = 0

        self.episode_durations = []
        self.episode_rewards = []

        plt.ion()

    def get_policy_action(self, state: torch.tensor) -> torch.tensor:
        sample = random.random()
        eps_threshold = self.eps_end + (self.eps_start - self.eps_end) * math.exp(-1. * self.steps_done / self.eps_decay)
        self.steps_done += 1
        if sample > eps_threshold:
            with torch.no_grad():
                action = self.policy_net(state)[0]
                return action
        else:
            return torch.tensor(self.env.action_space.sample(), device=self.device, dtype=torch.float32)
        
    def plot_durations(self, show_result: bool = False) -> None:
        plt.figure(1)
        durations_t = torch.tensor(self.episode_durations, dtype=torch.float)
        if show_result:
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Training...')
        plt.xlabel('Episode')
        plt.ylabel('Duration')
        plt.plot(durations_t.numpy())
        # Take 100 episode averages and plot them too
        if len(durations_t) >= 100:
            means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
            means = torch.cat((torch.zeros(99), means))
            plt.plot(means.numpy())

        plt.pause(0.001)  # pause a bit so that plots are updated

    def plot_rewards(self, show_result: bool = False) -> None:
        plt.figure(1)
        rewards_t = torch.tensor(self.episode_rewards, dtype=torch.float)
        if show_result:
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Training...')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.plot(rewards_t.numpy())
        # Take 100 episode averages and plot them too
        if len(rewards_t) >= 100:
            means = rewards_t.unfold(0, 100, 1).mean(1).view(-1)
            means = torch.cat((torch.zeros(99), means))
            plt.plot(means.numpy())

        plt.pause(0.001)  # pause a bit so that plots are updated

    def optimize_model(self):
        if len(self.memory) < self.batch_size:
            return
        transitions = self.memory.sample(self.batch_size)

        # Transpose the batch
        batch = Transition(*zip(*transitions))

        # Compute a mask of non-final states and concatenate the batch elements
        # (a final state would've been the one after which simulation ended)
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=self.device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.next_state
                                                    if s is not None])
        state_batch = torch.cat(batch.state)
        action_batch = torch.cat(batch.action)
        action_batch = action_batch.argmax(dim=1).view(state_batch.shape[0], 1)
        reward_batch = torch.cat(batch.reward)

        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
        # columns of actions taken. These are the actions which would've been taken
        # for each batch state according to policy_net
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states.
        # Expected values of actions for non_final_next_states are computed based
        # on the "older" target_net; selecting their best reward with max(1).values
        # This is merged based on the mask, such that we'll have either the expected
        # state value or 0 in case the state was final.
        next_state_values = torch.zeros(self.batch_size, device=self.device)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1).values
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch

        # Compute Huber loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values.squeeze(1), expected_state_action_values)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()

    def train(self, num_episodes: int = -1):
        if num_episodes < 0:
            if torch.backends.mps.is_available():
                num_episodes = 1000
            else:
                num_episodes = 50

        for i in range(num_episodes):
            if i % 50 == 0: print(i)

            options = None
            options = {'players' : [RandomPlayer(f"Player {i+1}") for i in range(self.env.player_count)], 'agent_idx' : random.choice(list(range(self.env.player_count))), 'reward_hyperparameters' : [0.1, -0.05, 1, -0.5, 20]}
            # options = {'players' : [GreedyPlayer(f"Player {i+1}") for i in range(self.env.player_count - 1)] + [HeuristicPlayer(f"Player {self.env.player_count}")], 'agent_idx' : 0, 'reward_hyperparameters' : [0.1, -0.05, 1, -0.5, 20]}
            # Initialize the environment and get its state
            state, _ = self.env.reset(options=options)
            state = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            for t in count():
                action = self.get_policy_action(state)
                observation, reward, terminated, truncated, info = self.env.step(action)
                reward = torch.tensor([reward], device=self.device)
                done = terminated or truncated

                if terminated:
                    next_state = None
                else:
                    next_state = torch.tensor(observation, dtype=torch.float32, device=self.device).unsqueeze(0)
                
                action = torch.zeros_like(action, dtype=torch.int64)
                action[info['action']] = 1
                # Store the transition in memory
                self.memory.push(state, action.unsqueeze(0), next_state, reward)

                # Move to the next state
                state = next_state

                # Perform one step of the optimization (on the policy network)
                self.optimize_model()

                # Soft update of the target network's weights
                target_net_state_dict = self.target_net.state_dict()
                policy_net_state_dict = self.policy_net.state_dict()
                for key in policy_net_state_dict:
                    target_net_state_dict[key] = policy_net_state_dict[key] * self.tau + target_net_state_dict[key] * (1 - self.tau)
                self.target_net.load_state_dict(target_net_state_dict)

                if done:
                    self.episode_durations.append(t + 1)
                    self.episode_rewards.append(reward.item())
                    self.plot_rewards()
                    # self.plot_durations()
                    break

        print('Complete')
        # self.plot_durations(show_result=True)
        self.plot_rewards(show_result=True)
        plt.ioff()
        plt.show()

        self.save_model(f"model_{self.env.player_count}_players_{num_episodes}_episodes.pt")

    def save_model(self, path: str):
        torch.save(self.policy_net.state_dict(), path)

def main():
    parser = ArgumentParser(description='Train a Deep Q-learning agent for Coup.')
    parser.add_argument('--player_count', '-n', type=int, default=2, help='the number of players')
    parser.add_argument('--num_episodes', '-e', type=int, default=-1, help='the number of episodes for training')

    args = parser.parse_args()
    env = Coup(args.player_count)

    trainer = Trainer(env, EPS_DECAY=args.num_episodes)

    trainer.train(args.num_episodes)

if __name__ == '__main__':
    main()