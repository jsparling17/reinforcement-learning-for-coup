import random
from player import Player
from representations import Action, Challenge, State
            

class Coup:
    """Simulates the game of Coup."""
    def __init__(self, player_count: int, provided_players: list[Player], round_cap: int = 100, print_public: bool = True, print_private: bool = False) -> None:
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
        self.round_cap: int = round_cap
        self.print_public: bool = print_public
        self.print_private: bool = print_private

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

    def get_state(self) -> State:
        """Returns the current public state of the game."""
        pass

    def valid_actions(self) -> list[Action]:
        """Returns a list of the valid actions or counteractions currently available to the active player."""
        pass

    def get_challenge(self, action: Action | None) -> Challenge | None:
        """If any players wish to challenge the given action, returns the challenge from the first player in turn order."""
        pass

    def get_counter(self, action: Action) -> Action | None:
        """If any players wish to take a counteraction to the give action, returns the counteraction."""
        pass
    
    # may update player cards, player coins, and remaining players
    def do_action(self, action: Action) -> None:
        """Performs the action or counteraction specified by the input."""
        pass

    # may update player cards and remaining players
    def do_challenge(self, challenge: Challenge | None) -> bool:
        """Performs the challenge specified by the input. Returns True if the challenge succeeds (and the action fails), and False otherwise. If the input is None, returns False."""
        pass
    
    def play(self) -> Player | None:
        """Simulates a game of Coup. Returns the winning player."""
        player_idx = random.randint(0, self.player_count - 1)

        while self.remaining_players > 1:
            player_idx = (player_idx + 1) % self.player_count
            self.active_player = self.players[player_idx]
            if len(self.active_player.cards) == 0:
                continue

            action = self.active_player.get_action(self.get_state(), self.valid_actions())
            
            challenge = self.get_challenge(action)

            if not self.do_challenge(challenge):
                counter = self.get_counter(action)
                challenge = self.get_challenge(counter)
                if self.do_challenge(challenge) or counter is None:
                    self.do_action()

            self.round += 1

            if self.round >= self.round_cap:
                return None
            
        return max(self.players, key=lambda x : len(x.cards))