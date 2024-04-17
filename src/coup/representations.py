from abc import ABC, abstractmethod
import random
import numpy as np
from dataclasses import dataclass


class State:
    """
    Represents the state of the game.\n
    Fields:\n
    players\n
    deck\n
    player_cards\n
    player_discards\n
    player_coins\n
    current_player
    """
    def __init__(self, players: list['Player']) -> None:
        assert len(players) <= 6

        self.players = players

        self.deck: list[int] = list(range(5)) * 3
        random.shuffle(self.deck)

        self.player_cards: dict[str, list[int]] = {}
        self.player_discards: dict[str, list[int]] = {}
        self.player_coins: dict[str, int] = {}
        
        for player in players:
            self.player_cards[player.name] = [self.deck.pop(), self.deck.pop()]
            self.player_discards[player.name] = []
            self.player_coins[player.name] = 2

        self.current_player = players[0]
    
    def encode(self, idx: int, player_count: int) -> np.NDArray[np.float32]:
        _, _, player_cards, player_discards, player_coins, _ = vars(self).values()
        player_names = list(player_discards.keys())
        name = player_names[idx]
        our_cards = player_cards[name]

        encoding = np.zeros((20 + 12 * player_count,))

        # fill [0 : 10] with information about our_cards
        if len(player_cards[name]) > 0:
            encoding[our_cards[0]] = 1
        if len(player_cards[name]) > 1:
            encoding[our_cards[1] + 5] = 1
        # fill [10 : 20] with more information about our_cards (if during an exchange)
        if len(player_cards[name]) > 2:
            encoding[our_cards[2] + 10] = 1
        if len(player_cards[name]) > 3:
            encoding[our_cards[3] + 15] = 1
        # fill [20 : 20 + player_count] with information about player_coins
        for i in range(player_count):
            player_name = player_names[i]
            encoding[20 + i] = player_coins[player_name] / 12
        # fill [20 + player_count : 20 + 11 * player_count] entries with information about player_discards
        for i in range(player_count):
            player_name = player_names[i]
            if len(player_discards[player_name]) > 0:
                encoding[20 + player_count + 10 * i + player_discards[player_name][0]] = 1
            if len(player_discards[player_name]) > 1:
                encoding[20 + player_count + 10 * i + 5 + player_discards[player_name][1]] = 1
        # fill [20 + 11 * player_count : 20 + 12 * player_count] with information about which player you are
        encoding[20 + 11 * player_count + idx] = 1

        return encoding

@dataclass
class Event(ABC):
    """
    Interface for game events (actions, counters, pair discards).
    """

    def __eq__(self, other: 'Event') -> bool:
        return vars(self) == vars(other)

    @abstractmethod
    def encode(self, state: State, player_count: int) -> np.NDArray[np.float32]:
        pass


class Action(Event):
    """
    Represents an action.\n
    Fields:\n
    active_player\n
    target_player\n
    type
    """

    active_player: str
    target_player: str
    type: int

    def encode(self, state: State, player_count: int) -> np.NDArray[np.float32]:
        encoding = np.zeros((4 * player_count + 4,))
        active, target, action_type = vars(self).values()
        player_names = list(state.player_discards.keys())

        # encode the sender
        encoding[player_names.index(active)] = 1

        # encode the action_type along with target
        if action_type == 'Income':
            encoding[player_count] = 1
        elif action_type == 'Foreign Aid':
            encoding[player_count + 1] = 1
        elif action_type == 'Tax':
            encoding[player_count + 2] = 1
        elif action_type == 'Exchange':
            encoding[player_count + 3] = 1
        elif action_type == 'Steal':
            encoding[player_count + 4 + player_names.index(target)] = 1
        elif action_type == 'Assassinate':
            encoding[2 * player_count + 4 + player_names.index(target)] = 1 
        elif action_type == 'Coup':
            encoding[3 * player_count + 4 + player_names.index(target)] = 1
        else:
            exit(1)

        return encoding
    

class Counter(Event):
    """
    Represents a challenge or a block.\n
    Fields:\n
    active_player\n
    attempted\n
    challenge\n
    counter_1
    """

    active_player: str
    attempted: bool  # true if the challenge or block is attempted
    challenge: bool  # true if the counter is a challenge, false if it's a block
    counter_1: bool  # true if the counter is a 1st order counter, false if counter-counter

    def encode(self, state: State, player_count: int) -> np.NDArray[np.float32]:
        active, attempted, challenge, counter_1 = vars(self).values()

        if counter_1:
            encoding = np.zeros((3 + player_count,))
            
            # encode accept / challenge / block
            if not attempted:
                encoding[0] = 1
            elif challenge:
                encoding[1] = 1
            else:
                encoding[2] = 1

            # encode the blocker
            if attempted:
                player_names = list(state.player_discards.keys())
                encoding[3 + player_names.index(active)] = 1

        else:
            encoding = np.zeros((2 + player_count,))

            if not attempted:
                encoding[0] = 1
            else:
                encoding[1] = 1

            # encode the blocker
            if attempted:
                player_names = list(state.player_discards.keys())
                encoding[2 + player_names.index(active)] = 1

        return encoding
    

class DiscardPair(Event):
    """
    Represents the cards discarded to the Exchange action.\n
    Fields:\n
    initial_cards\n
    discard_idxs
    """

    initial_cards: list[int]
    discard_idxs: list[int]

    def encode(self) -> np.NDArray[np.float32]:
        encoding = np.zeros((26,))
        initial_cards, discard_idxs = vars(self).values()

        for i, card in enumerate(initial_cards):
            encoding[5 * i + card] = 1

        # encode the card_idxs
        idxs_to_encoding = {frozenset({0, 1}): 20,
                            frozenset({0, 2}): 21,
                            frozenset({0, 3}): 22,
                            frozenset({1, 2}): 23,
                            frozenset({1, 3}): 24,
                            frozenset({2, 3}): 25}
        
        encoding[idxs_to_encoding[frozenset(discard_idxs)]] = 1

        return encoding
    

class Player(ABC):
    """
    Interface for players.
    """

    def __init__(self, name: str = 'Bot') -> None:
        self.name: str = name

    @abstractmethod
    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        """Selects a valid action given a game state and history."""
        pass

    @abstractmethod
    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        """Decides whether to take a counteraction given a game state and history."""
        pass

    @abstractmethod
    def get_discard(self, state: State, history: list[Event]) -> int:
        """Decides which card to discard given a game state and history."""
        pass

    @abstractmethod
    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        """Decides which pair of cards to discard given a game state and history."""
        pass