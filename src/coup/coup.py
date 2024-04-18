import gymnasium as gym
import numpy as np
from gymnasium import spaces
import random
from typing import Any

from coup.representations import Action, Counter, State, Event, DiscardPair, Player
from coup.player import HeuristicPlayer
from coup.utils import *


class Coup(gym.Env):
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
        self.player_count: int = player_count
        self.round_cap: int = round_cap
        self.history_length: int = history_length

    def step(self, action: np.NDArray) -> tuple[np.NDArray, np.float32, bool, bool, dict[str, Any]]:
        gs: State = self.game_state

        self._decode_action(action)

        self._run_phase_transition()

        terminated = (self.players[self.agent_idx] not in gs.players) or (len(gs.players) == 1)
        if not terminated:
            self._run_game_until_input()

        observation = self._observation()
        reward = self._reward()
        terminated = (self.players[self.agent_idx] not in gs.players) or (len(gs.players) == 1)
        truncated = self.round > self.round_cap
        info = {}

        return observation, reward, terminated, truncated, info

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
            self.agent_idx: int = random.choice(list(range(self.player_count)))
            self.reward_hyperparameters: list[int] = [0.1, -0.05, 1, -0.5, 20]
        else:
            self.players: list[Player] = options['players']
            self.agent_idx: int = options['agent_idx']
            self.reward_hyperparameters: list[int] = options['reward_hyperparameters']

        self.game_state: State = State(self.players)
        self.history: list[Event] = []
        self.phase: str = "action"

        self.round: int = 0


    def render(self) -> None:
        pass

    def close(self) -> None:
        pass

    def _run_game_until_input(self) -> None:
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
        
        gs: State = self.game_state
        
        if self.phase == "action":
            self.current_action: Action = Action('', '', -2)
            self.current_counter_1: Counter = Counter('', False, False, True)
            self.current_counter_2: Counter = Counter('', False, True, False)
            self.current_discard: list[tuple[Player, int]] = []
            self.current_discard_pair: list[int] = []
            self.current_discarders: list[Player] = []
            self.current_counter_1_queried: list[Player] = []
            self.current_counter_2_queried: list[Player] = []

            if self._decision_is_agent(gs.current_player): 
                return 
            else:
                self.current_action = gs.current_player.get_action(self.game_state, self.history, generate_valid_actions(gs.current_player, gs.players, gs.player_coins, gs.player_cards))
                self._action_phase_transition()
            
        elif self.phase == "counter_1":
            for player in [p for p in gs.players if p.name != gs.current_player.name]:
                if player in self.current_counter_1_queried: continue
                self.current_counter_1_queried.append(player)
                if self._decision_is_agent(player):
                    return 
                else:
                    potential_counter_1 = player.get_counter(self.current_action, self.game_state, self.history, generate_valid_counters(player, self.current_action))
                    if potential_counter_1.attempted:
                        self.current_counter_1 = potential_counter_1
                        break
            self._counter_1_phase_transition()

        elif self.phase == "counter_2":

            for player in [p for p in gs.players if p.name != self.current_counter_1.active_player]:
                if player in self.current_counter_2_queried: continue
                self.current_counter_2_queried.append(player)
                if self._decision_is_agent(player):
                    return
                else:
                    action = Action(self.current_counter_1.active_player, self.current_counter_1.active_player, -1)
                    potential_counter_2 = player.get_counter(action, self.game_state, self.history, generate_valid_counters(player, action), action_is_block=True)
                    if potential_counter_2.attempted:
                        self.current_counter_2 = potential_counter_2
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

            gs.player_cards[gs.current_player.name] += [gs.deck.pop(), gs.deck.pop()]
            if self._decision_is_agent(gs.current_player):
                return
            else:
                self.current_discard_pair = gs.current_player.get_discard_pair(self.game_state, self.history)
                self._discard_pair_phase_transition()
        else:
            exit(1)

        self._run_game_until_input()

    def _run_phase_transition(self) -> None:
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

    def _action_phase_transition(self) -> None:
        self.history.append(self.current_action)
        if self.current_action.type == 0:
            self.phase = "action"
            self._simulate_turn()
        elif self.current_action.type == 6:
            self.phase = "discard"
        else:
            self.phase = "counter_1"

    def _counter_1_phase_transition(self) -> None:
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

    def _counter_2_phase_transition(self) -> None:
        if len(self.current_counter_2_queried) < self.player_count - 1: 
            self.phase = "counter_2"
        self.history.append(self.current_counter_2)
        if not self.current_counter_2.attempted:
            self.phase = "action"
            self._simulate_turn()
        else:
            self.phase = "dispose"

    def _discard_phase_transition(self) -> None:
        if self.current_action.type == 3:
            active_cards = self.game_state.player_cards[self.current_action.active_player]
            if not action_bluffed(self.current_action.type, active_cards):
                self.phase = "keep"
            else:
                self.phase = "action"
                self._simulate_turn()
        else:
            self.phase = "action"
            self._simulate_turn()

    def _discard_pair_phase_transition(self) -> None:
        gs: State = self.game_state
        self.history.append(DiscardPair(self.players.index(gs.current_player), gs.player_cards[gs.current_player.name].copy(), self.current_discard))
        self.phase = "action"
        self._simulate_turn()

    def _simulate_turn(self) -> None:
        self.round += 1
        gs: State = self.game_state
        action_type: int = self.current_action.type

        if self.current_counter_1.attempted:
            if self.current_counter_2.attempted:
                counter_cards = gs.player_cards[self.current_counter_1.active_player]
                if not bool(set(ACTION_IDX_BLOCKER[type]).intersection(set(counter_cards))):
                    card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_counter_1.active_player][0]
                    lose_challenge(self.current_counter_1.active_player, gs.player_cards, card_idx, gs.player_discards)
                    self._take_action()
                else:
                    card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_counter_2.active_player][0]
                    lose_challenge(self.current_counter_2.active_player, gs.player_cards, card_idx, gs.player_discards)

            else:
                if self.current_counter_1.challenge:
                    active_cards = gs.player_cards[self.current_action.active_player]
                    if action_bluffed(action_type, active_cards):
                        card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_action.active_player][0]
                        lose_challenge(self.current_action.active_player, gs.player_cards, card_idx, gs.player_discards)
                    else:
                        card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_counter_1.active_player][0]
                        lose_challenge(self.current_counter_1.active_player, gs.player_cards, card_idx, gs.player_discards)
                        self._take_action()

        else:
            self._take_action()

        self._update_next_player()

    def _take_action(self) -> None:
        gs: State = self.game_state
        p1: str = self.current_action.active_player
        p2: str = self.current_action.target_player
        action_type: int = self.current_action.type

        match action_type:
            case 0:
                income(p1, gs.player_coins)
            case 1:
                foreign_aid(p1, gs.player_coins)
            case 2:
                tax(p1, gs.player_coins)
            case 3:
                cards = gs.player_cards[gs.current_player.name].copy()
                cards_idxs = self.current_discard
                exchange(p1, gs.player_cards, cards, cards_idxs, gs.deck)
            case 4:
                steal(p1, p2, gs.player_coins)
            case 5:
                if len(gs.player_cards[p2]) > 0:
                    card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_action.target_player][0]
                    assassinate(p1, p2, gs.player_coins, gs.player_coins, card_idx, gs.player_discards)
            case 6:
                card_idx = [disc[1] for disc in self.current_discard if disc[0].name == self.current_action.target_player][0]
                coup(p1, p2, gs.player_coins, gs.player_coins, card_idx, gs.player_discards)
            case _:
                return

    def _update_next_player(self) -> None:
        gs: State = self.game_state

        gs.players = gs.players[1:] + [gs.players[0]]
        gs.players = [p for p in gs.players if len(gs.player_cards[p.name]) > 0]
        gs.player_coins = { p : (c if len(gs.player_cards[p]) > 0 else 0) for p, c in zip(gs.player_coins.keys(), gs.player_coins.values())}
        gs.current_player = gs.players[0]

    def _determine_discarders(self) -> list[Player]:
        discarders: list[Player] = []
        gs: State = self.game_state
        action_type: int = self.current_action.type

        if self.current_counter_1.attempted:
            if self.current_counter_2.attempted:
                counter_cards = gs.player_cards[self.current_counter_1.active_player]
                if counter_1_bluffed(action_type, counter_cards):
                    discarders.append([p for p in gs.players if p.name == self.current_counter_1.active_player][0])
                    if action_type in [5, 6]:
                        discarders.append([p for p in gs.players if p.name == self.current_action.target_player][0])
                else:
                    discarders.append([p for p in gs.players if p.name == self.current_counter_2.active_player][0])
                
            else:
                if self.current_counter_2.challenge:
                    active_cards = gs.player_cards[self.current_action.active_player]
                    if action_bluffed(action_type, active_cards):
                        discarders.append([p for p in gs.players if p.name == self.current_action.active_player][0])
                    else:
                        discarders.append([p for p in gs.players if p.name == self.current_counter_2.active_player][0])
                        if action_type in [5, 6]:
                            discarders.append([p for p in gs.players if p.name == self.current_action.target_player][0])

        else:
            if action_type in [5, 6]:
                discarders.append([p for p in gs.players if p.name == self.current_action.target_player][0])
        
        return discarders


    def _observation(self) -> np.NDArray[np.float32]:
        return np.concatenate((self.game_state.encode(), self._encode_history()))

    def _encode_history(self) -> np.NDArray[np.float32]:
        """
        Return an np array of size (35 + 6 * player_count) * history_length that encodes the information from the last history_length turns.

        history_length turns:
            4 + 4 * player_count : action phase, 4 actions on oneself, 3 actions on other players, sender
            3 + player_count  : counter_1 phase, 3 (accept, challenge, block) + player_count (blocker)
            2 + player_count  : counter_2 phase, 2 (accept, challenge) + player_count (blocker)
            26     : discard_pair phase  , 4 * 5 roles + (4 choose 2)

        self.history is stored as the following:
        [action: Action, counter_1: Counter, action: Action, counter_1: Counter, discard_pair: DiscardPair, ...]

        action fields       : active, target , type 
        counter fields      : active, attempted, challenge, counter_1
        discard_pair fields : initial_cards , discard_idxs

        Note: dispose is not a relevant action to store in the memory. 
        Note: keeps are only stored for the agent
        """

        encoding: np.NDArray[np.float32] = np.zeros(((6 * self.player_count + 35) * self.history_length,))
        encoded_turns: int = 0
        event_encoding: np.NDArray[np.float32] = np.zeros((6 * self.player_count + 35,))
        for event in reversed(self.history):
            if encoded_turns == self.history_length:
                return encoding
            if isinstance(event, Action):
                event_encoding[0:4 + 4 * self.player_count] = event.encode()
                encoding[(6 * self.player_count + 35) * encoded_turns:(6 * self.player_count + 35) * (encoded_turns + 1)] = event_encoding
                encoded_turns += 1
                event_encoding = np.zeros((6 * self.n + 35,))
            elif isinstance(event, Counter):
                if event.counter_1:
                    event_encoding[4 + 4 * self.player_count:7 + 5 * self.player_count] = event.encode()
                else:
                    event_encoding[7 + 5 * self.player_count:9 + 6 * self.player_count] = event.encode()
            elif isinstance(event, DiscardPair) and event.active_player_idx == self.agent_idx:
                event_encoding[9 + 6 * self.player_count:35 + 6 * self.player_count] = event.encode()
        return encoding

    def _decode_action(self, a: np.NDArray[np.float32]) -> None:
        """
        Return an action, counter, discard, or discard_pair based on the np array, a.
        
        action_size = 4 + 3 * (player_count - 1) # 4 actions on oneself, 3 actions on other players
        counter_1_size = 3 # accept, challenge, block
        counter_2_size = 2 # accept, challenge
        discard_size = 2 # remove card 1 or card 2
        discard_pair_size = 6 # (4 choose 2)
        """

        gs: State = self.game_state

        player_names = list(gs.player_discards.keys())
        if self.phase == "action":
            a = a[0:1 + 3 * self.player_count]
            possible_actions = generate_valid_actions(gs.current_player, gs.players, gs.player_coins, gs.player_cards)
            list_of_players = list([p_name for p_name in gs.player_discards.keys() if p_name != player_names[self.agent_idx]])
            idx_to_player = {i : list_of_players[i] for i in range(len(list_of_players))}
            idx_to_type = {0: 'Income', 1: 'Foreign Aid', 2: 'Tax', 3: 'Exchange'}

            for i in range(4, 3 + self.player_count):
                idx_to_type[i] = 'Steal'
            for i in range(3 + self.player_count, 2 + 2 * self.player_count):
                idx_to_type[i] = 'Assassinate'
            for i in range(2 + 2 * self.player_count, 1 + 3 * self.player_count):
                idx_to_type[i] = 'Coup'

            action = None
            while action not in possible_actions:
                i = np.argmax(a)
                a[i] = -1 * float('inf')
                type = ACTION_INDICES[idx_to_type[i]]
                if i > 3:
                    target = idx_to_player[(i - 4) % (self.player_count - 1)]
                else:
                    target = player_names[self.agent_idx]
                action = Action(player_names[self.agent_idx], target, type)
            self.current_action = action

        elif self.phase == "counter_1":
            a = a[1 + 3 * self.player_count:4 + 3 * self.player_count]
            possible_counters = generate_valid_counters(player_names[self.agent_idx], self.current_action)

            counter_1 = None
            while counter_1 not in possible_counters:
                i = np.argmax(a)
                a[i] = -1 * float('inf')
                if i == 0: # accept
                    block1 = Counter(player_names[self.agent_idx], False, False, True)
                if i == 1: # challenge
                    block1 = Counter(player_names[self.agent_idx], True, True, True)
                if i == 2: # block
                    block1 = Counter(player_names[self.agent_idx], True, False, True)
            self.current_counter_1 = counter_1

        elif self.phase == "counter_2":
            a = a[4 + 3 * self.player_count:6 + 3 * self.player_count]
            counter_1 = self.current_counter_1
            if counter_1.challenge:
                counter_1 = Action(counter_1.active_player, player_names[self.agent_idx], -2)
            else:
                counter_1 = Action(counter_1.active_player, player_names[self.agent_idx], -1)
            possible_counters = generate_valid_counters(player_names[self.agent_idx], counter_1)

            counter_2 = None
            while counter_2 not in possible_counters:
                i = np.argmax(a)
                a[i] = -1 * float('inf')
                if i == 0: # accept
                    counter_2 = Counter(player_names[self.agent_idx], False, False, True)
                if i == 1: # challenge
                    counter_2 = Counter(player_names[self.agent_idx], True, True, True)  
            self.current_counter_2 = counter_2

        elif self.phase == "discard":
            a = a[6 + 3 * self.player_count:8 + 3 * self.player_count]
            i = np.argmax(a)
            if len(gs.player_discards[player_names[self.agent_idx]]) > 0:
                i = 0
            self.current_discard.append((self.players[self.agent_idx], i))

        elif self.phase == "discard_pair":
            a = a[8 + 3 * self.player_count:14 + 3 * self.player_count]
            i = np.argmax(a)
            idx_to_discard = {0: [0, 1],
                            1: [0, 2],
                            2: [0, 3],
                            3: [1, 2],
                            4: [1, 3],
                            5: [2, 3]}
            self.current_discard = idx_to_discard[i]

        else:
            exit(1)

    def _reward(self) -> np.float32:
        COIN_VALUE, OPP_COIN_VALUE, CARD_VALUE, OPP_CARD_VALUE, WIN_VALUE = self.reward_hyperparameters

        gs: State = self.game_state

        reward = 0

        reward += COIN_VALUE * gs.player_coins[self.players[self.agent_idx].name]
        reward += OPP_COIN_VALUE * sum([gs.player_coins[self.players[i].name] for i in range(self.player_count) if i != self.agent_idx])
        reward += CARD_VALUE * len(gs.player_cards[self.players[self.agent_idx].name])
        reward += OPP_CARD_VALUE * sum([len(gs.player_cards[self.players[i].name]) for i in range(self.player_count) if i != self.agent_idx])
        if all(self.players[self.agent_idx].name == p for p in [p.name for p in gs.players]):
            reward += WIN_VALUE
        elif self.players[self.agent_idx].name not in [p.name for p in gs.players]:
            reward += -1 * WIN_VALUE

        return reward
    
    def _decision_is_agent(self, player: Player) -> bool:
        player_names = list(self.game_state.player_discards.keys())
        return self.agent_idx == player_names.index(player.name)