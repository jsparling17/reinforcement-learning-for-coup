import random
from player import Player
from representations import Representation, Action, Challenge, State, PrivateState
            

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
        self.history: dict[int, list[Representation]] = {i : [] for i in range(self.round_cap)}

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
        index = random.randint(0, len(self.deck) - 1)
        card = self.deck[index]
        del self.deck[index]
        return card

    def get_state(self) -> State:
        """Returns the current public state of the game."""
        return State(self.players, self.active_player)

    def get_private_state(self) -> PrivateState:
        """Returns the current complete state of the game."""
        return PrivateState(self.players, self.active_player)

    def valid_actions(self) -> list[Action]:
        """Returns a list of the valid actions currently available to the active player."""
        coins = self.active_player.coins
        player_idx = self.active_player.index
        if coins >= 10:
            # must stage coup if 10+ coins
            return [Action(2, player_idx, i) for i in range(self.player_count) if i != player_idx]
        
        actions = []

        # could take income
        actions += [Action(0, player_idx)]

        # could take foreign aid
        actions += [Action(1, player_idx)]

        if coins >= 7:
            # could stage a coup against each other player
            return [Action(2, player_idx, i) for i in range(self.player_count) if i != player_idx]
        
        # could exchange
        actions += [Action(3, player_idx)]

        if coins >= 3:
            # could assassinate each other player
            actions += [Action(4, player_idx, i) for i in range(self.player_count) if i != player_idx]
        
        # could steal from each other player with coins
        actions += [Action(5, player_idx, i) for i in range(self.player_count) if i != player_idx and self.players[i].coins > 0]

        # could tax
        actions += [Action(6, player_idx)]

        return actions

    def valid_counteractions(self, action: Action, player_idx: int) -> list[Action]:
        """Returns a list of the valid counteractions currently available to the given player."""
        target_player_idx = self.active_player.index
        if action.type in {1, 4, 5}:
            return [Action(action.type, player_idx, target_player_idx, True)]
        return []


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

    def print_history(self) -> None:
        """Prints the complete transcript of a game."""
        pass
    
    def play(self) -> Player | None:
        """Simulates a game of Coup. Returns the winning player."""
        player_idx = random.randint(0, self.player_count - 1)

        while self.remaining_players > 1:
            player_idx = (player_idx + 1) % self.player_count
            self.active_player = self.players[player_idx]
            if len(self.active_player.cards) == 0:
                continue
            
            self.history[self.round].append(self.get_private_state())

            state = self.get_state()
            if self.print_public:
                print(f'Round {self.round}:\n', state)
            action = self.active_player.get_action(state, self.valid_actions())

            self.history[self.round].append(action)
            if self.print_public:
                print(action)
            
            challenge = self.get_challenge(action)

            if not self.do_challenge(challenge):
                if challenge is not None:
                    self.history[self.round].append(challenge)
                    self.history[self.round].append(self.get_private_state())
                    if self.print_public:
                        print(challenge, 'The challenge is unsuccessful.\n', self.get_state())

                counter = self.get_counter(action)
                if counter is not None:
                    self.history[self.round].append(counter)
                    print(counter)
                challenge = self.get_challenge(counter)
                if self.do_challenge(challenge) or counter is None:
                    if challenge is not None:
                        self.history[self.round].append(challenge)
                        self.history[self.round].append(self.get_private_state())
                        print(challenge, 'The challenge is successful.\n', self.get_state())
                    
                    self.do_action()
                else:
                    if challenge is not None:
                        self.history[self.round].append(challenge)
                        self.history[self.round].append(self.get_private_state())
                        print(challenge, 'The challenge is unsuccessful.\n', self.get_state())
            else:
                self.history[self.round].append(challenge)
                self.history[self.round].append(self.get_private_state())
                print(challenge, 'The challenge is successful.\n', self.get_state())
            

            self.round += 1

            if self.round >= self.round_cap:
                if self.print_private:
                    self.print_history()
                return None
        
        if self.print_private:
            self.print_history()
        return max(self.players, key=lambda x : len(x.cards))