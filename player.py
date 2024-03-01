import random
from abc import ABC, abstractmethod

from representations import Action, Challenge, State, ExchangeCards


class Player(ABC):
    """Interface for players."""

    def __init__(self, index: int = 0, cards: list[int] = [0, 0], coins: int = 2, name: str = 'Bot', is_bot: bool = True) -> None:
        self.index: int = index
        self.cards: list[int] = cards
        self.discarded_cards: list[int] = []
        self.coins: int = coins
        self.name: str = name
        self.is_bot: bool = is_bot

    @abstractmethod
    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        pass
    
    @abstractmethod
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        pass

    @abstractmethod
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        pass

    @abstractmethod
    def lose_card(self) -> int:
        pass

    @abstractmethod
    def choose_cards(self, state: State) -> list[int]:
        pass

    @abstractmethod
    def show_card(self, card: int) -> None:
        pass
        
class GreedyPlayer(Player):
    """A player that always assassinates a random opponent with among the least cards when possible,\
        taxes otherwise, uses counteractions when it has the appropriate cards, and never challenges."""

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        assassinations = [action for action in valid_actions if action.type == 4]
        if len(assassinations) > 0:
            return random.choice(assassinations)
        
        tax = Action(6, state.active_player)
        if tax in valid_actions:
            return tax
        
        return random.choice(valid_actions)
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        return None
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        for action in valid_actions:
            if action.type == 1 and 4 in self.cards:
                # block foreign aid
                return Action
            if action.type == 4 and 3 in self.cards:
                # block assassination
                return Action
            if action.type == 5 and 0 in self.cards or 2 in self.cards:
                # block foreign aid
                return Action
            return None

    def lose_card(self) -> int:
        assassins_idx = [i for i in range(len(self.cards)) if self.cards[i] == 1]
        dukes_idx = [i for i in range(len(self.cards)) if self.cards[i] == 4]

        useful_idx = assassins_idx + dukes_idx

        lose_idx = -1
        for i in range(len(self.cards)):
            if i not in useful_idx:
                lose_idx = i
                break
        
        if lose_idx < 0:
            for i in range(len(self.cards)):
                if i not in assassins_idx:
                    lose_idx = i
                    break
        
        lose_idx = 0
        
        card = self.cards[lose_idx]
        del self.cards[lose_idx]
        self.discarded_cards.append(card)
        return card
            

    def choose_cards(self, state: State) -> list[int]:
        cards = [self.lose_card() for i in range(2)]
        return cards

    def show_card(self, card: int) -> None:
        idx = self.cards.index(card)
        del self.cards[idx]