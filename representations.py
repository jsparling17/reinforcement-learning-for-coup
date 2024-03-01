from abc import ABC, abstractmethod


class Representation(ABC):
    """Interface for representations of an aspect of the game."""

    @abstractmethod
    def __str__(self) -> str:
        pass


class Action(Representation):
    """Represents an action or counteraction."""

    def __init__(self, action_type: int, active_player: int, target_player: int = -1, is_counter: bool = False) -> None:
        self.type: int = action_type
        self.active_player: int = active_player
        self.target_player: int = target_player
        self.is_counter: bool = is_counter

    def __eq__(self, other: 'Action') -> bool:
        return self.type == other.type and\
               self.active_player == other.active_player and\
               self.target_player == other.target_player and\
               self.is_counter == other.is_counter

    def action_str(self) -> str:
        match self.type:
            case 0:
                rep = 'take Income (1 coin).\n'
            case 1:
                if self.is_counter:
                    rep = f'block player {self.target_player} from taking Foreign Aid.\n'
                else:
                    rep = 'take Foreign Aid (2 coins).\n'
            case 2:
                rep = f'stage a Coup against player {self.target_player}.\n'
            case 3:
                rep = 'Exchange cards with the deck.\n'
            case 4:
                if self.is_counter:
                    rep = f'block player {self.target_player} from Assassinating.\n'
                else:
                    rep = f'Assassinate player {self.target_player}.\n'
            case 5:
                if self.is_counter:
                    rep = f'block player {self.target_player} from Stealing.\n'
                else:
                    rep = f'Steal from player {self.target_player}.\n'
            case 6:
                rep = 'take Tax (3 coins).\n'
            
        return rep

    def __str__(self) -> str:
        rep = f'Player {self.active_player} tries to '
        rep += self.action_str()
        return rep
    

class Challenge(Representation):
    """Represents a challenge to an action."""

    def __init__(self, action: Action, active_player: int, target_player: int) -> None:
        self.action: Action = action
        self.active_player: int = active_player
        self.target_player: int = target_player

    def __str__(self) -> str:
        rep = f'Player {self.active_player} challenges player {self.target_player}\'s attempt to '
        rep += self.action.action_str()
        return rep


class State(Representation):
    """Represents the public state of the game.\n
       Fields:\n
       self.revealed_cards\n
       self.coins\n
       self.card_counts\n
       self.active_player"""
    
    # maps card number representation to name of card; i.e. self.card_names[i] gives the name of the card represented by i
    card_names: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']
    
    def __init__(self, players: list['Player'], active_player: int):
        self.revealed_cards: list[list[int]] = [player.discarded_cards for player in players]
        self.coins: list[int] = [player.coins for player in players]
        self.card_counts: list[int] = [len(player.cards) for player in players]
        self.active_player: int = active_player

    def __str__(self) -> str:
        rep = f'The state of the game is as follows:\nThe active player is player {self.active_player}.\n'
        for i in range(len(self.revealed_cards)):
            match len(self.revealed_cards[i]):
                case 0:
                    rep += f'Player {i} has 2 cards and {self.coins[i]} coins.\n'
                case 1:
                    rep += f'Player {i} has 1 card, having discarded the {self.card_names[self.revealed_cards[i][0]]}, and {self.coins[i]} coins.\n'
                case 2:
                    rep += f'Player {i} has been eliminated, having discarded the {" and ".join([self.card_names[self.revealed_cards[i][j]] for j in range(2)])}.\n'
                case _:
                    raise Exception('ERROR! A player has discarded more than 2 cards.')
        
        return rep
    

class PrivateState(State):
    """Represents the complete state of the game."""

    def __init__(self, players: list['Player'], active_player: int):
        super(PrivateState, self).__init__(players, active_player)

        self.hidden_cards: list[list[int]] = [player.cards for player in players]

    def __str__(self) -> str:
        rep = f'The state of the game is as follows:\nThe active player is player {self.active_player}.\n'
        for i in range(len(self.revealed_cards)):
            match len(self.revealed_cards[i]):
                case 0:
                    rep += f'Player {i} has 2 cards: the {" and ".join([self.card_names[self.hidden_cards[i][j]] for j in range(2)])}, and {self.coins[i]} coins.\n'
                case 1:
                    rep += f'Player {i} has 1 card, the {self.card_names[self.hidden_cards[i][0]]}, having discarded the {self.card_names[self.revealed_cards[i][0]]}, and {self.coins[i]} coins.\n'
                case 2:
                    rep += f'Player {i} has been eliminated, having discarded the {" and ".join([self.card_names[self.revealed_cards[i][j]] for j in range(2)])}.\n'
                case _:
                    raise Exception('ERROR! A player has discarded more than 2 cards.')
                
        return rep
    
class ExchangeCards(Representation):
    """Represents the cards draw with the Exchange action."""

    # maps card number representation to name of card; i.e. self.card_names[i] gives the name of the card represented by i
    card_names: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']

    def __init__(self, cards: list[int]) -> None:
        self.cards: list[int] = cards

    def __str__(self) -> str:
        return f'A player returned the {" and ".join([self.card_names[self.cards[i]] for i in range(2)])} to the deck.\n'
    

class Player(ABC):
    """Interface for players."""

    # maps card number representation to name of card; i.e. self.card_names[i] gives the name of the card represented by i
    card_names: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']

    def __init__(self, index: int = 0, cards: list[int] = [0, 0], coins: int = 2, name: str = 'Bot', is_bot: bool = True) -> None:
        self.index: int = index
        self.cards: list[int] = cards
        self.discarded_cards: list[int] = []
        self.coins: int = coins
        self.name: str = name
        self.is_bot: bool = is_bot

    def __str__(self) -> str:
        return f'Player {self.name} is in position {self.index} with card(s) {" and ".join([self.card_names[i] for i in self.cards])} and {self.coins} coins.\nPlayer {self.name} is {"not " if not self.is_bot else ""}a bot.\n'

    @abstractmethod
    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        """Selects a valid action given a game state."""
        pass
    
    @abstractmethod
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        """Decides whether to challenge a given action given a game state."""
        pass

    @abstractmethod
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        """Decides whether to take a counteraction given a game state."""
        pass

    @abstractmethod
    def lose_card(self, state: State) -> int:
        """Decides which card to discard given a game state."""
        pass

    @abstractmethod
    def choose_cards(self, state: State) -> list[int]:
        """Decides which cards to return to the deck for the Exchange action."""
        pass

    @abstractmethod
    def show_card(self, card: int) -> None:
        """Removes a given card from the player's hand as the result of a unsuccessful challenge."""
        pass