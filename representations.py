from player import Player

class State:
    """Represents the public state of the game."""
    
    # maps card number representation to name of card; i.e. self.card_names[i] gives the name of the card represented by i
    card_names: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']
    
    def __init__(self, players: list[Player], active_player: int):
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
                    rep += f'Player {i} has been eliminated, having discarded the {' and '.join([self.card_names[self.revealed_cards[i][j]] for j in range(2)])}.\n'
                case _:
                    raise Exception('ERROR! A player has discarded more than 2 cards.')
        
        return rep
    

class Action:
    """Represents an action or counteraction."""

    def __init__(self, action_type: int, active_player: int, target_player: int = -1, is_counter: bool = False) -> None:
        self.type = action_type
        self.active_player = active_player
        self.target_player = target_player
        self.is_counter = is_counter

    def __str__(self) -> str:
        rep = f'Player {self.active_player}'
        match self.type:
            case 0:
                rep += ' takes Income (1 coin).\n'
            case 1:
                if self.is_counter:
                    rep += f' blocks player {self.target_player} from taking Foreign Aid.\n'
                else:
                    rep += ' takes Foreign Aid (2 coins).\n'
            case 2:
                rep += f' stages a Coup against player {self.target_player}.\n'
            case 3:
                rep += ' Exchanges cards with the deck.\n'
            case 4:
                if self.is_counter:
                    rep += f' blocks player {self.target_player} from Assassinating them.\n'
                else:
                    rep += f' Assassinates player {self.target_player}.\n'
            case 5:
                if self.is_counter:
                    rep += f' blocks player {self.target_player} from Stealing from them.\n'
                else:
                    rep += f' Steals from player {self.target_player}.\n'
            case 6:
                rep += ' takes Tax (3 coins).\n'
            
        return rep