import random

from player import Player
from representations import Representation, Action, Challenge, State, PrivateState, ExchangeCards
            

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
            player.cards = [self.draw_card() for i in range(2)]
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

        for i in range(1, self.player_count):
            player_idx = (i + self.active_player.index) % self.player_count
            player = self.players[player_idx]
            if len(player.cards) != 0:
                challenge = player.get_challenge(self.get_state, Action)
                if challenge is not None:
                    return challenge
                
        return None

    def get_counter(self, action: Action) -> Action | None:
        """If any players wish to take a counteraction to the give action, returns the counteraction."""

        for i in range(1, self.player_count):
            player_idx = (i + self.active_player.index) % self.player_count
            player = self.players[player_idx]
            if len(player.cards) != 0:
                counter = player.get_counteraction(self.get_state, self.valid_counteractions(action, player_idx))
                if counter is not None:
                    self.history[self.round].append(counter)
                    if self.print_public:
                        print(counter)
                    return counter
                
        return None
    
    # may update player cards, player coins, and remaining players
    def do_action(self, action: Action) -> None:
        """Performs the action specified by the input."""

        active_player = self.players[action.active_player]
        if action.target_player >= 0:
            target_player = self.players[action.target_player]

        action_type = action.type

        if action_type == 0:
            # income
            active_player.coins += 1

        elif action_type == 1:
            # foreign aid
            active_player.coins += 2

        elif action_type == 2:
            # coup
            active_player.coins -= 7
            target_player.lose_card()

        elif action_type == 3:
            # exchange
            drawn_cards = [self.draw_card() for i in range(2)]
            self.history[self.round].append(ExchangeCards(drawn_cards))
            active_player.cards += drawn_cards
            discarded = active_player.choose_cards(self.get_state())
            self.deck += discarded

        elif action_type == 4:
            # assassinate
            active_player.coins -= 3
            target_player.lose_card()

        elif action_type == 5:
            # steal
            coins = max(2, target_player.coins)
            active_player.coins += coins
            target_player.coins -= coins

        elif action_type == 6:
            # tax
            active_player.coins += 3
            

    # may update player cards and remaining players
    def do_challenge(self, challenge: Challenge | None) -> bool:
        """Performs the challenge specified by the input. Returns True if the challenge succeeds (and the action fails), and False otherwise. If the input is None, returns False."""

        if challenge is None: 
            return False
        
        self.history[self.round].append(challenge)
        self.history[self.round].append(self.get_private_state())
        
        card = self.action_mapping[challenge.action.type]

        target_player = self.players[challenge.target_player]
        active_player = self.players[challenge.active_player]

        if card in target_player.cards:
            target_player.show_card(card)
            self.deck.append(card)
            target_player.cards.append(self.draw_card())
            active_player.lose_card()

            if self.print_public:
                print(challenge, 'The challenge is unsuccessful.\n', self.get_state())

            return False
        else:
            target_player.lose_card()

            print(challenge, 'The challenge is successful.\n', self.get_state())

            return True


    def record_action(self, state: State, action: Action) -> None:
        """Prints and records in the game history the state before an action and the action."""

        self.history[self.round].append(self.get_private_state())
        self.history[self.round].append(action)

        if self.print_public:
            print(f'Round {self.round}:\n', state)
            print(action)

    def print_history(self) -> None:
        """Prints the complete transcript of a game."""

        for round in self.history:
            print(f'Round {round}:\n', "".join(self.history[round]))
    
    def play(self) -> Player | None:
        """Simulates a game of Coup. Returns the winning player."""

        player_idx = random.randint(0, self.player_count - 1)

        while self.remaining_players > 1:
            player_idx = (player_idx + 1) % self.player_count
            self.active_player = self.players[player_idx]
            if len(self.active_player.cards) == 0:
                continue
            
            state = self.get_state()

            action = self.active_player.get_action(state, self.valid_actions())
            self.record_action(state, action)
            
            challenge = self.get_challenge(action)

            if not self.do_challenge(challenge):
                counter = self.get_counter(action)
                challenge = self.get_challenge(counter)
                if self.do_challenge(challenge) or counter is None:
                    self.do_action()
            
            self.round += 1

            if self.round >= self.round_cap:
                if self.print_private:
                    self.print_history()
                return None
        
        if self.print_private:
            self.print_history()
        return max(self.players, key=lambda x : len(x.cards))