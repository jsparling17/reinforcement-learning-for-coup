import random
from player import Player

class Coup:
    def __init__(self, player_count: int, provided_players: list[Player]) -> None:
        if player_count < 2 or player_count > 6:
            raise Exception('ERROR! The player count must be between 2 and 6.')

        if len(provided_players) > player_count:
            raise Exception('ERROR! The number of provided players cannot exceed the specified player count.')
        
        self.deck: list[int] = []

        # maps card number representation to name of card; i.e. self.card_mapping[i] gives the name of the card represented by i
        self.card_mapping: dict[int, str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']

        self.players: list[Player] = []
        self.round: int = 0
        self.active_player: Player = None
        self.target_player: Player = None
        self.player_count: int = player_count
        self.remaining_players: int = player_count

        # maps action number representation to associated card, or -1 if there isn't one; i.e. self.action_mapping[i] gives the card for action i
        self.action_mapping: list[int] = [-1, -1, -1, 0, 1, 2, 4]

        for player in provided_players:
            self.players.append(player)

        for i in range(player_count - len(provided_players)):
            player = Player(name=i, is_bot=True)
            self.players.append(player)
        
        self.reset_game()

    def reset_game(self) -> None:
        self.deck = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
        self.round = 0
        self.active_player = None
        self.target_player = None

        for player in self.players:
            player.cards = [self.draw_card for i in range(2)]
            player.coins = 2
        
    def draw_card(self) -> int:
        index = random.randint(0, len(self.deck)-1)
        card = self.deck[index]
        del self.deck[index]
        return card