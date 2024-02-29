import random
from player import Player

class State:
    """Represents the public state of the game."""
    def __init__(self, players: list[Player], active_player: int):
        self.revealed_cards: list[list[int]] = [player.discarded_cards for player in players]
        self.coins: list[int] = [player.coins for player in players]
        self.card_counts: list[int] = [len(player.cards) for player in players]
        self.active_player: int = active_player

class Coup:
    """Simulates the game of Coup."""
    def __init__(self, player_count: int, provided_players: list[Player]) -> None:
        if player_count < 2 or player_count > 6:
            raise Exception('ERROR! The player count must be between 2 and 6.')

        if len(provided_players) > player_count:
            raise Exception('ERROR! The number of provided players cannot exceed the specified player count.')
        
        self.deck: list[int] = []

        # maps card number representation to name of card; i.e. self.card_names[i] gives the name of the card represented by i
        self.card_names: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']

        self.players: list[Player] = []
        self.round: int = 0
        self.active_player: Player = None
        self.target_player: Player = None
        self.player_count: int = player_count
        self.remaining_players: int = player_count

        # maps action number representation to name of action; i.e. self.action_names[i] gives the name of the action represented by i
        self.action_names: list[str] = ['Income', 'Foreign Aid', 'Coup', 'Exchange', 'Assassinate', 'Steal', 'Tax']

        # maps action number representation to associated card, or -1 if there isn't one; i.e. self.action_mapping[i] gives the card for action i
        self.action_mapping: list[int] = [-1, -1, -1, 0, 1, 2, 4]

        for i in range(player_count - len(provided_players)):
            player = Player(name=i, is_bot=True)
            self.players.append(player)

        self.players += provided_players
        
        self.reset_game()

    def reset_game(self) -> None:
        """Resets the deck to contain one of each card, resets the round counter to 0, deals new cards to each player, and sets each player's coin total to 2."""
        self.deck = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
        self.round = 0
        self.active_player = None
        self.target_player = None

        for i, player in enumerate(self.players):
            player.cards = [self.draw_card for i in range(2)]
            player.coins = 2
            player.index = i
        
    def draw_card(self) -> int:
        """Returns (and removes from the deck) a card drawn at random."""
        index = random.randint(0, len(self.deck)-1)
        card = self.deck[index]
        del self.deck[index]
        return card
    
    def do_action(self, action: int) -> None:
        """Performs the action specified by the input value given the current active and targeted players."""
        pass

    def do_counteraction(self, counteraction: int) -> None:
        """Performs the counteraction specified by the input value given the current active and targeted players."""
        pass

    def do_challenge(self) -> None:
        pass

    def get_state(self) -> State:
        pass
    
    def play(self):
        player_idx = random.randint(0, self.player_count - 1)

        while self.remaining_players > 1:
            self.active_player = self.players[player_idx]
