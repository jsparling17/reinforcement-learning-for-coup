import numpy as np
import random
import math
from collections import deque
from itertools import count

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from agent import ReplayBuffer, DQN
from coup import Coup
from representations import Action, Challenge, State, Player


class TrainingPlayer(Player):
    """A player used to train the Deep Q Learning network."""

    # BATCH_SIZE is the number of transitions sampled from the replay buffer
    # GAMMA is the discount factor
    # EPS_START is the starting value of epsilon
    # EPS_END is the final value of epsilon
    # EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
    # TAU is the update rate of the target network
    # LR is the learning rate of the AdamW optimizer
    # STATE_SIZE is the dimension of the input vector representing the state of the game
    # ACTION_COUNT is the dimension of the output vector representing actions

    def __init__(self, BATCH_SIZE: int = 128, GAMMA: float = 0.99,
                 EPS_START: float = 0.9, EPS_END: float = 0.05,
                 EPS_DECAY: float = 1000, TAU: float = 0.005,
                 LR: float = 1e-4, STATE_SIZE: int = 13, ACTION_COUNT: int = 9):
        
        super(TrainingPlayer, self).__init__()
        
        self.batch_size = BATCH_SIZE
        self.gamma = GAMMA
        self.eps_start = EPS_START
        self.eps_end = EPS_END
        self.eps_decay = EPS_DECAY
        self.tau = TAU
        self.lr = LR
        self.state_size = STATE_SIZE
        self.action_count = ACTION_COUNT

        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        self.policy_net = DQN(STATE_SIZE, ACTION_COUNT).to(self.device)
        self.target_net = DQN(STATE_SIZE, ACTION_COUNT).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=LR, amsgrad=True)
        self.memory = ReplayBuffer(10000)

        self.steps_done = 0

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        pass
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        pass
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        pass

    def get_policy_action(self, state: torch.tensor) -> torch.tensor:
        sample = random.random()
        eps_threshold = self.eps_end + (self.eps_start - self.eps_end) * \
            math.exp(-1. * self.steps_done / self.eps_decay)
        self.steps_done += 1
        if sample > eps_threshold:
            with torch.no_grad():
                # t.max(1) will return the largest column value of each row.
                # second column on max result is index of where max element was
                # found, so we pick action with the larger expected reward.
                return self.policy_net(state).max(1).indices.view(1, 1)
        else:
            return torch.tensor([[env.action_space.sample()]], device=self.device, dtype=torch.long)
        
    def choose_card(self, state: State) -> int:
        pass


def main():
    pass

if __name__ == '__main__':
    main()