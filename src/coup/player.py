import random
import torch
from itertools import combinations

from coup.representations import Event, Action, Counter, State, Player
from coup.utils import *


class HeuristicPlayer(Player):
    """A player that follows a relatively effective heuristic."""

    # TODO: add tracking for which cards opponent has (e.g. for relevant counteractions)

    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        cards = state.player_cards[self.name]

        coups = [action for action in valid_actions if action.type == 6]
        if len(coups) > 0:
            max_cards = max([len(state.player_cards[action.target_player]) for action in coups])
            return random.choice([action for action in coups if len(state.player_cards[action.target_player]) == max_cards])
        
        if (1 in cards and random.random() < 0.8) or (1 not in cards and random.random() < 0.2):
            assassinations = [action for action in valid_actions if action.type == 5]
            if len(assassinations) > 0:
                max_cards = max([len(state.player_cards[action.target_player]) for action in assassinations])
                return random.choice([action for action in assassinations if len(state.player_cards[action.target_player]) == max_cards])
            
        tax = [action for action in valid_actions if action.type == 2]
        if tax and (4 in cards):
            return tax[0]
            
        thefts = [action for action in valid_actions if action.type == 4]
        if len(thefts) > 0:
            max_coins = max([state.player_coins[action.target_player] for action in thefts])
            if max_coins > 0 and (2 in cards):
                return random.choice([action for action in thefts if state.player_coins[action.target_player] == max_coins])
            
        rand = random.random()
        if rand < 0.5:
            income = [action for action in valid_actions if action.type == 0]
            if income:
                return income[0]
            
        elif rand < 0.75:
            if tax:
                return tax[0]
            
            if len(thefts) > 0 and max_coins > 0:
                return random.choice([action for action in thefts if state.player_coins[action.target_player] == max_coins])
        
        return random.choice(valid_actions)
    
    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        if action_is_block:
            if random.random() < 0.2:
                return Counter(self.name, True, True, False)
            else:
                return Counter(self.name, False, False, False)
            
        cards = state.player_cards[self.name]

        if action.type == 1 and 4 in cards:
            # block foreign aid
            return Counter(self.name, True, False, True)
        if action.type == 5 and 3 in cards:
            # block assassination
            return Counter(self.name, True, False, True)
        if action.type == 4 and (0 in cards or 2 in cards):
            # block theft
            return Counter(self.name, True, False, True)
        
        if random.random() < 0.4:
            counter = random.choice(valid_counters)
            return counter
        
        return Counter(self.name, False, False, True)
        
    def get_discard(self, state: State, history: list[Event]) -> int:

        cards = state.player_cards[self.name]

        if 0 in cards:
            return cards.index(0)
        
        if 3 in cards:
            return cards.index(3)
        
        if 4 in cards:
            return cards.index(4)
        
        if 2 in cards:
            return cards.index(2)
        
        if 1 in cards:
            return cards.index(1)
        
        return 0
    
    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        cards = state.player_cards[self.name]

        card_indices = [[] for i in range(5)]

        for i, card in enumerate(cards):
            card_indices[card].append(i)

        discards = []

        while len(card_indices[0]) > 0 and len(discards) < 2:
            discards.append(card_indices[0].pop())

        if len(discards) == 2:
            return discards
        
        while len(card_indices[3]) > 1 and len(discards) < 2:
            discards.append(card_indices[3].pop())

        if len(discards) == 2:
            return discards
        
        while len(card_indices[4]) > 1 and len(discards) < 2:
            discards.append(card_indices[4].pop())

        if len(discards) == 2:
            return discards
        
        while len(card_indices[2]) > 1 and len(discards) < 2:
            discards.append(card_indices[2].pop())

        if len(discards) == 2:
            return discards
        
        while len(card_indices[1]) > 1 and len(discards) < 2:
            discards.append(card_indices[1].pop())

        if len(discards) == 2:
            return discards

        if len(card_indices[3]) == 1:
            discards.append(card_indices[3].pop())

        if len(discards) == 2:
            return discards
        
        if len(card_indices[4]) == 1:
            discards.append(card_indices[4].pop())

        if len(discards) == 2:
            return discards
        
        return random.sample(list(range(len(cards))), k=2)


class GreedyPlayer(Player):
    """A player that always assassinates an opponent when possible, taxes otherwise, uses counteractions when it has the appropriate cards, and never challenges."""

    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        cards = state.player_cards[self.name]
        assassinations = [action for action in valid_actions if action.type == 5]
        if len(assassinations) > 0:
            max_cards = max([len(state.player_cards[action.target_player]) for action in assassinations])
            return random.choice([action for action in assassinations if len(state.player_cards[action.target_player]) == max_cards])
        
        tax = [action for action in valid_actions if action.type == 2]
        if tax:
            return tax[0]
        
        return random.choice(valid_actions)
    
    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        if action_is_block:
            return Counter(self.name, False, False, False)
            
        cards = state.player_cards[self.name]

        if action.type == 1 and 4 in cards:
            # block foreign aid
            return Counter(self.name, True, False, True)
        if action.type == 5 and 3 in cards:
            # block assassination
            return Counter(self.name, True, False, True)
        if action.type == 4 and (0 in cards or 2 in cards):
            # block theft
            return Counter(self.name, True, False, True)
        
        return Counter(self.name, False, False, True)
        
    def get_discard(self, state: State, history: list[Event]) -> int:
        cards = state.player_cards[self.name]

        assassins_idx = [i for i in range(len(cards)) if cards[i] == 1]
        dukes_idx = [i for i in range(len(cards)) if cards[i] == 4]

        useful_idx = assassins_idx + dukes_idx

        lose_idx = -1
        for i in range(len(cards)):
            if i not in useful_idx:
                lose_idx = i
                break
        
        if lose_idx < 0:
            for i in range(len(cards)):
                if i not in assassins_idx:
                    lose_idx = i
                    break
        
            lose_idx = 0

        return lose_idx
    
    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        return [0, 1]
    

class PiratePlayer(Player):
    """A player that always assassinates an opponent when possible, steals from the richest opponent otherwise, uses counteractions when it has the appropriate cards, and never challenges."""

    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        assassinations = [action for action in valid_actions if action.type == 5]
        if len(assassinations) > 0:
            max_cards = max([len(state.player_cards[action.target_player]) for action in assassinations])
            return random.choice([action for action in assassinations if len(state.player_cards[action.target_player]) == max_cards])
        
        thefts = [action for action in valid_actions if action.type == 4]
        if len(thefts) > 0:
            max_coins = max([state.player_coins[action.target_player] for action in thefts])
            if max_coins > 0:
                return random.choice([action for action in thefts if state.player_coins[action.target_player] == max_coins])
        
        return random.choice(valid_actions)
    
    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        if action_is_block:
            return Counter(self.name, False, False, False)
            
        cards = state.player_cards[self.name]

        if action.type == 1 and 4 in cards:
            # block foreign aid
            return Counter(self.name, True, False, True)
        if action.type == 5 and 3 in cards:
            # block assassination
            return Counter(self.name, True, False, True)
        if action.type == 4 and (0 in cards or 2 in cards):
            # block theft
            return Counter(self.name, True, False, True)
        
        return Counter(self.name, False, False, True)
        
    def get_discard(self, state: State, history: list[Event]) -> int:
        cards = state.player_cards[self.name]

        assassins_idx = [i for i in range(len(cards)) if cards[i] == 1]
        dukes_idx = [i for i in range(len(cards)) if cards[i] == 4]

        useful_idx = assassins_idx + dukes_idx

        lose_idx = -1
        for i in range(len(cards)):
            if i not in useful_idx:
                lose_idx = i
                break
        
        if lose_idx < 0:
            for i in range(len(cards)):
                if i not in assassins_idx:
                    lose_idx = i
                    break
        
            lose_idx = 0

        return lose_idx
    
    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        return [0, 1]
    
    
class RandomPlayer(Player):
    """
    A player that selects actions at random.
    """

    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        return random.choice(valid_actions)

    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        return random.choice(valid_counters)

    def get_discard(self, state: State, history: list[Event]) -> int:
        return random.choice([0, 1])

    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        cards = state.player_cards[self.name]
        return random.choice(list(combinations(range(len(cards)), 2)))

class DummyPlayer(Player):
    """
    A stand-in player.
    """

    def get_action(self, state: State, history: list[Event], valid_actions: list[Action]) -> Action:
        return valid_actions[0]

    def get_counter(self, action: Action, state: State, history: list[Event], valid_counters: list[Counter], action_is_block: bool = False) -> Counter:
        return valid_counters[0]

    def get_discard(self, state: State, history: list[Event]) -> int:
        return 0

    def get_discard_pair(self, state: State, history: list[Event]) -> list[int]:
        return [0, 1]