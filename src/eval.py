import numpy as np
import gymnasium as gym
import random
import math
import matplotlib
import matplotlib.pyplot as plt
from itertools import count
from argparse import ArgumentParser

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from agent import DQN
from coup.coup import Coup
from coup.player import GreedyPlayer, HeuristicPlayer, RandomPlayer
from coup.utils import *

class Evaluator:
    """A class used to evaluate DQN players for Coup."""

    def __init__(self, env: Coup, model: DQN) -> None:

        self.env: Coup = env

        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        self.model: DQN = model.to(self.device)

        self.games_played: int = 0
        self.games_won: int = 0

        # stores [games_played, games_won]
        self.games_by_start_hand: dict[tuple[int, int], list[int]] = {}
        
        for i in range(5):
            for j in range(i + 1):
                self.games_by_start_hand[(j, i)] = [0, 0]

    def get_start_cards_from_encoding(self, observation: torch.Tensor) -> tuple[int, int]:
        card1 = (observation[:5] == 1).nonzero().item()
        card2 = (observation[5:10] == 1).nonzero().item()
        if card1 > card2:
            card1, card2 = card2, card1

        return (card1, card2)
            

    def eval(self, num_episodes: int = -1, player_type: str = "g", display: bool = True):
        if num_episodes < 0:
            if torch.backends.mps.is_available():
                num_episodes = 1000
            else:
                num_episodes = 50

        for i in range(num_episodes):
            if i % 50 == 0 and display: print(i)

            agent_idx = random.choice(list(range(self.env.player_count)))

            match player_type:
                case "g":
                    players = [GreedyPlayer(f"Player {i+1}") for i in range(self.env.player_count)]
                case "r":
                    players = [RandomPlayer(f"Player {i+1}") for i in range(self.env.player_count)]
                case "h":
                    players = [HeuristicPlayer(f"Player {i+1}") for i in range(self.env.player_count)]
                case _:
                    players = [GreedyPlayer(f"Player {i+1}") for i in range(self.env.player_count)]

            options = {'players' : players, 'agent_idx' : agent_idx, 'reward_hyperparameters' : [0.1, -0.05, 1, -0.5, 20]}

            # Initialize the environment and get its state
            state, _ = self.env.reset(options=options)
            state = torch.tensor(state, dtype=torch.float32, device=self.device)

            start_cards = self.get_start_cards_from_encoding(state)
            
            state = state.unsqueeze(0)

            for t in count():
                with torch.no_grad():
                    action = self.model(state)[0]
                observation, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated

                if terminated:
                    next_state = None
                else:
                    next_state = torch.tensor(observation, dtype=torch.float32, device=self.device).unsqueeze(0)

                # Move to the next state
                state = next_state

                if done:
                    self.games_played += 1
                    self.games_by_start_hand[start_cards][0] += 1
                    if reward >= 20:
                        self.games_won += 1
                        self.games_by_start_hand[start_cards][1] += 1
                    break
            
        if display:
            print(f"win rate: {round(100 * self.games_won / self.games_played, 1)}%")
            print("win rate by starting hand: ")

            for i in range(5):
                for j in range(i + 1):
                    cards = (j, i)
                    print(f"{', '.join(list(CARD_NAMES[k] for k in cards))}: {round(100 * self.games_by_start_hand[cards][1] / self.games_by_start_hand[cards][0], 1)}%")
        
        return self.games_won / self.games_played

def main():
    parser = ArgumentParser(description='Evaluate a Deep Q-learning agent for Coup.')
    parser.add_argument('--player_count', '-n', type=int, default=2, help='the number of players')
    parser.add_argument('--player_type', '-p', type=str, default="g", help='the type of players to evaluate against: r(andom), g(reedy), h(euristic)')
    parser.add_argument('--num_episodes', '-e', type=int, default=-1, help='the number of episodes for evaluation')
    parser.add_argument('--model_path', '-m', type=str, help='the path to the model to be evaluated')


    args = parser.parse_args()
    env = Coup(args.player_count)

    model: DQN = DQN(env.observation_space.shape[0], env.action_space.shape[0])
    model.load_state_dict(torch.load(args.model_path))
    model.eval()

    evaluator = Evaluator(env, model)

    evaluator.eval(args.num_episodes, args.player_type)

if __name__ == '__main__':
    main()