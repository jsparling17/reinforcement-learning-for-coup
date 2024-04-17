import gymnasium as gym
import numpy as np
from gymnasium import spaces
import random
from typing import Any

from coup.representations import State, Event, DiscardPair, Player
from coup.player import HeuristicPlayer
from coup.utils import *


class Coup(gym.env):
    """
    Simulates the game of Coup following the gym interface.  
    """

    def __init__(self, player_count: int, round_cap: int = 100, history_length = 10) -> None:
        super().__init__()

        action_count: int = 4 + 3 * (player_count - 1)  # 4 solo actions, 3 targeted actions
        counter_1_count: int = 3  # accept, challenge, block
        counter_2_count: int = 2  # accept, challenge
        discard_count: int = 2  # discard either card
        discard_pair: int = 6  # 4c2

        action_dim: int = action_count + counter_1_count + counter_2_count + discard_count + discard_pair

        game_state_dim: int = 4 * 5 + 12 * player_count  # up to 4 cards, 5 options each, coins per player, up to 2 discarded cards per player, 5 options each, which player is the agent
        history_dim: int = (35 + 6 * player_count) * history_length  # provides last batch of events

        observation_dim: int = game_state_dim + history_dim

        self.action_space = spaces.Box(low=0, high=1, shape=(action_dim,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(observation_dim,), dtype=np.float32)

        self.player_count, self.round_cap, self.history_length = player_count, round_cap, history_length

    def step(self, action: np.NDArray) -> tuple[np.NDArray, np.float32, bool, bool, dict[str, Any]]:
        pass

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[np.NDArray[np.float32], dict[str, Any]]:
        """
        options:
        - 'players': specifices the agents to use as opponents
        - 'agent_idx': specifies which player the RL agent is
        - 'reward_hyperparameters': specifies the values of features to be rewarded
            * number of agent's coins
            * number of opponents' coins
            * number of agent's cards
            * number of opponents' cards
            * value of winning

        usage:
            options = {'players': [GreedyPlayer(f"Player {i+1}") for i in range(self.player_count)], 'agent_idx': 0}
        """

        if options == None:
            self.players: list[Player] = [HeuristicPlayer(f"Player {i + 1}") for i in range(self.player_count)]

            self.agent_idx, self.reward_hyperparameters = random.choice(list(range(self.player_count))), [0.1, -0.05, 1, -0.5, 20]
        else:
            self.players, self.agent_idx, self.reward_hyperparameters = options['players'], options['agent_idx'], options['reward_hyperparameters']

        self.game_state: State = State(self.players)
        self.history: list[Event] = []
        self.phase = "action"

        self.round = 0


    def render(self) -> None:
        pass

    def close(self) -> None:
        pass

    def _run_game_until_input(self):
        """
        Runs the game until an input from the agent specified by self.agent_idx is required to continue. 

        Modifies self.game_state, self.history, self.phase

        self.phase is one of the following: "action", "counter_1", "counter_2", "discard", or "discard_pair"

        action: get action_action from current player
        counter_1: get action_block1 from all players besides current player (stop if dispute or block)
        counter_2: get action_block2 from all players besides block1er (stop if dispute)
        discard: get action_dispose from player who lost a card
        discard_pair: get action_keep from player who exchanged successfully
        """

        if (self.players[self.agent_idx] not in self.game_state.players) or (len(self.game_state.players) == 1):
            return
        
        players, deck, player_cards, player_discards, player_coins, current_player = vars(self.game_state).values()
        
        if self.phase == "action":
            self.current_action, self.current_counter_1, self.current_counter_2, self.current_discard, self.current_discard_pair = None, None, None, [], None
            self.current_discarders, self.current_counter_1_queried, self.current_counter_2_queried = [], [], []

            if self._decision_is_agent(current_player): 
                return 
            else:
                self.current_action = current_player.get_action(self.game_state, self.history, generate_valid_actions(current_player, players, player_coins, player_cards))
                self._action_phase_transition()
            
        elif self.phase == "counter_1":
            for player in [p for p in players if p.name != current_player.name]:
                if player in self.current_counter_1_queried: continue
                self.current_counter_1_queried.append(player)
                if self._decision_is_agent(player):
                    return 
                else:
                    potential_counter_1 = player.get_counter(self.current_action, self.game_state, self.history, generate_valid_counters(player, self.current_action))
                    if potential_counter_1.attempted:
                        self.self.current_counter_1 = potential_counter_1
                        break
            self._counter_1_phase_transition()

        elif self.phase == "counter_2":

            for player in [p for p in players if p.name != self.current_counter_1.active_player]:
                if player in self.current_counter_2_queried: continue
                self.current_counter_2_queried.append(player)
                if self._decision_is_agent(player):
                    return
                else:
                    action = Action(self.current_counter_1.active_player, self.current_counter_1.active_player, -1)
                    potential_counter_2 = player.get_counter(action, self.game_state, self.history, generate_valid_counters(player, action), action_is_block=True)
                    if potential_counter_2.attempted:
                        self.current_block2 = potential_counter_2
                        break
            self._counter_2_phase_transition()

        elif self.phase == "discard":
            if not self.current_discarders: self.current_discarders = self._determine_discarders()

            agent_discard = False
            for discarder in self.current_discarders:
                if self._decision_is_agent(discarder):
                    agent_discard = True
                    continue
                else:
                    self.current_discard.append((discarder, discarder.get_discard(self.game_state, self.history)))
            if agent_discard:
                return
            self._discard_phase_transition()

        elif self.phase == "discard_pair":

            player_cards[current_player.name] += [deck.pop(), deck.pop()]
            if self._decision_is_agent(current_player):
                return
            else:
                self.current_discard_pair = current_player.get_discard_pair(self.game_state, self.history)
                self._discard_pair_phase_transition()
        else:
            exit(1)

        self._run_game_until_input()

    def _run_phase_transition(self):
        if self.phase == "action":
            self._action_phase_transition()
        elif self.phase == "counter_1":
            self._counter_1_phase_transition()
        elif self.phase == "counter_2":
            self._counter_2_phase_transition()
        elif self.phase == "discard":
            self._discard_phase_transition()
        elif self.phase == "discard_pair":
            self._discard_pair_phase_transition()
        else:
            exit(1)

    def _action_phase_transition(self):
        self.history.append(self.current_action)
        if self.current_action.type == 0:
            self.phase = "action"
            self._simulate_turn()
        elif self.current_action.type == 6:
            self.phase = "discard"
        else:
            self.phase = "counter_1"

    def _counter_1_phase_transition(self):
        if len(self.current_counter_1_queried) < self.player_count - 1: 
            self.phase = "counter_1"
        self.history.append(self.current_counter_1)
        if not self.current_counter_1.attempted:
            if self.current_action.type == 5:
                self.phase = "discard"
            elif self.current_action.type == 3:
                self.phase = "discard_pair"
            else:
                self.phase = "action"
                self._simulate_turn()
        else:
            if self.current_counter_1.challenge:
                self.phase = "discard"
            else:
                self.phase = "counter_2"

    def _counter_2_phase_transition(self):
        if len(self.current_counter_2_queried) < self.player_count - 1: 
            self.phase = "counter_2"
        self.history.append(self.current_counter_2)
        if not self.current_counter_2.attempted:
            self.phase = "action"
            self._simulate_turn()
        else:
            self.phase = "dispose"

    def _discard_phase_transition(self):
        if self.current_action.type == 3:
            player_cards = self.game_state.player_cards
            active_cards = player_cards[self.current_action.active_player]
            if ACTION_IDX_CARD[self.current_action.type] in active_cards:
                self.phase = "keep"
            else:
                self.phase = "action"
                self._simulate_turn()
        else:
            self.phase = "action"
            self._simulate_turn()

    def _discard_pair_phase_transition(self):
        self.history.append(DiscardPair(self.game_state.player_cards[self.game_state.current_player.name].copy(), self.current_discard))
        self.phase = "action"
        self._simulate_turn()

    def _simulate_turn(self):
        pass

    def income(player_name, player_coins):
        player_coins[player_name] += 1

    def foreign_aid(player_name, player_coins):
        player_coins[player_name] += 2

    def tax(player_name, player_coins):
        player_coins[player_name] += 3

    def steal(player1_name, player2_name, player_coins):
        player_coins[player1_name] += min(player_coins[player2_name], 2)
        player_coins[player2_name] -= min(player_coins[player2_name], 2)

    def coup(player1_name, player2_name, player_coins, player_cards, card_idx, player_discards):
        player_coins[player1_name] -= 7
        if len(player_cards[player2_name]) < 2: card_idx = 0
        lost_card = player_cards[player2_name].pop(card_idx)
        player_discards[player2_name].append(lost_card)

    def assassinate(player1_name, player2_name, player_coins, player_cards, card_idx, player_discards):
        player_coins[player1_name] -= 3
        if len(player_cards[player2_name]) < 2: card_idx = 0
        lost_card = player_cards[player2_name].pop(card_idx)
        player_discards[player2_name].append(lost_card)

    def lose_block(player_name, player_cards, card_idx, player_discards):
        if len(player_cards[player_name]) < 2: card_idx = 0
        lost_card = player_cards[player_name].pop(card_idx)
        player_discards[player_name].append(lost_card)

    def exchange(player_name, player_cards, cards, cards_idxs, deck):
        player_cards[player_name] = [cards[idx] for idx in cards_idxs]
        for idx in cards_idxs:
            cards[idx] = None
        cards = [c for c in cards if c != None]
        deck += cards

    def _take_action(self):
        pass

    def _update_next_player(self):
        pass

    def _determine_discarders(self):
        pass

    def _observation(self):
        pass

    def _encode_history(self):
        pass

    def _decode_action(self, a: np.NDArray[np.float32]):
        pass

    def _reward(self):
        pass
    
    def _decision_is_agent(self, player: Player) -> bool:
        player_names = list(self.game_state.player_discards.keys())
        return self.agent_idx == player_names.index(player.name)