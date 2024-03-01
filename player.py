import random

from representations import Action, Challenge, State, Player

        
class GreedyPlayer(Player):
    """A player that always assassinates an opponent when possible, taxes otherwise, uses counteractions when it has the appropriate cards, and never challenges."""

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        assassinations = [action for action in valid_actions if action.type == 4]
        if len(assassinations) > 0:
            max_cards = max([state.card_counts[action.target_player] for action in assassinations])
            return random.choice([action for action in assassinations if state.card_counts[action.target_player] == max_cards])
        
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
                return action
            if action.type == 4 and 3 in self.cards:
                # block assassination
                return action
            if action.type == 5 and 0 in self.cards or 2 in self.cards:
                # block foreign aid
                return action
            return None
        
    def choose_card(self, state: State) -> int:
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

        return lose_idx

    def lose_card(self, state: State) -> int:
        lose_idx = self.choose_card(state)
        card = self.cards[lose_idx]
        del self.cards[lose_idx]
        self.discarded_cards.append(card)
        return card
            

    def choose_cards(self, state: State) -> list[int]:
        cards = []
        for i in range(2):
            lose_idx = self.choose_card(state)
            cards.append(self.cards[lose_idx])
            del self.cards[lose_idx]
        return cards

    def show_card(self, card: int) -> None:
        idx = self.cards.index(card)
        del self.cards[idx]

class PiratePlayer(Player):
    """A player that always assassinates an opponent when possible, steals from the richest opponent otherwise, uses counteractions when it has the appropriate cards, and never challenges."""

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        assassinations = [action for action in valid_actions if action.type == 4]
        if len(assassinations) > 0:
            max_cards = max([state.card_counts[action.target_player] for action in assassinations])
            return random.choice([action for action in assassinations if state.card_counts[action.target_player] == max_cards])
        
        thefts = [action for action in valid_actions if action.type == 5]
        if len(thefts) > 0:
            max_coins = max([state.coins[action.target_player] for action in thefts])
            return random.choice([action for action in thefts if state.coins[action.target_player] == max_coins])
        
        return random.choice(valid_actions)
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        return None
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        for action in valid_actions:
            if action.type == 1 and 4 in self.cards:
                # block foreign aid
                return action
            if action.type == 4 and 3 in self.cards:
                # block assassination
                return action
            if action.type == 5 and (0 in self.cards or 2 in self.cards):
                # block steal
                return action
        return None
    
    def choose_card(self, state: State) -> int:
        assassins_idx = [i for i in range(len(self.cards)) if self.cards[i] == 1]
        captains_idx = [i for i in range(len(self.cards)) if self.cards[i] == 2]

        useful_idx = assassins_idx + captains_idx

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

        return lose_idx

    def lose_card(self, state: State) -> int:
        lose_idx = self.choose_card(state)
        card = self.cards[lose_idx]
        del self.cards[lose_idx]
        self.discarded_cards.append(card)
        return card
            

    def choose_cards(self, state: State) -> list[int]:
        cards = []
        for i in range(2):
            lose_idx = self.choose_card(state)
            cards.append(self.cards[lose_idx])
            del self.cards[lose_idx]
        return cards

    def show_card(self, card: int) -> None:
        idx = self.cards.index(card)
        del self.cards[idx]

class UserPlayer(Player):
    """A player controlled by the user."""

    def __init__(self, index: int = 0, cards: list[int] = [0, 0], coins: int = 2, name: str = 'Bot', is_bot: bool = True) -> None:
        super(UserPlayer, self).__init__(index=index, cards=cards, coins=coins, name=name, is_bot=False)

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        print(state)
        newline = '\n'
        print(f'Your position is {self.index}.')
        print(f'You have the {" and ".join([self.card_names[i] for i in self.cards])}.')
        print(f'You have {self.coins} coins.')
        print(f'Your available actions are as follows:\n\n{newline.join(["  " + str(action) for action in valid_actions])}')
        print('USAGE: <action type> <target player if the action requires a target>')

        while True:
            response = input()
            
            match response.split():
                case [action_type]:
                    for action in valid_actions:
                        if action.type == int(action_type) and action.target_player == -1:
                            return action
                    print('USAGE: <action type> <target player if the action requires a target>')
                    continue
                case [action_type, target_player]:
                    for action in valid_actions:
                        if action.type == int(action_type) and action.target_player == int(target_player):
                            return action
                    print('USAGE: <action type> <target player if the action requires a target>')
                    continue
                case _:
                    print('USAGE: <action type> <target player if the action requires a target>')
                    continue
                
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        return None
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        for action in valid_actions:
            if action.type == 1 and 4 in self.cards:
                # block foreign aid
                return action
            if action.type == 4 and 3 in self.cards:
                # block assassination
                return action
            if action.type == 5 and (0 in self.cards or 2 in self.cards):
                # block steal
                return action
        return None

    def choose_card(self, state: State) -> int:
        if len(self.cards) == 1:
            return 0
        
        print(state)
        print(f'Choose a card to discard. You have the {" and ".join([self.card_names[i] for i in self.cards])}.')
        print('USAGE: <card number>')

        while True:
            response = input()
            if response.isdigit() and int(response) in self.cards:
                lose_idx = self.cards.index(int(response))
                break
            print('USAGE: <card number>')
        
        return lose_idx

    def lose_card(self, state: State) -> int:
        lose_idx = self.choose_card(state)
        card = self.cards[lose_idx]
        del self.cards[lose_idx]
        self.discarded_cards.append(card)
        return card
            

    def choose_cards(self, state: State) -> list[int]:
        cards = []
        for i in range(2):
            lose_idx = self.choose_card(state)
            cards.append(self.cards[lose_idx])
            del self.cards[lose_idx]
        return cards

    def show_card(self, card: int) -> None:
        idx = self.cards.index(card)
        del self.cards[idx]