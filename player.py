import random
import torch

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


class HeuristicPlayer(Player):
    """A player that follows a relatively effective heuristic."""

    # TODO: add tracking for which cards opponent has (e.g. for relevant counteractions)

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:

        coups = [action for action in valid_actions if action.type == 2]
        if len(coups) > 0:
            max_cards = max([state.card_counts[action.target_player] for action in coups])
            return random.choice([action for action in coups if state.card_counts[action.target_player] == max_cards])
        
        if (1 in self.cards and random.random() < 0.8) or (1 not in self.cards and random.random() < 0.2):
            assassinations = [action for action in valid_actions if action.type == 4]
            if len(assassinations) > 0:
                max_cards = max([state.card_counts[action.target_player] for action in assassinations])
                return random.choice([action for action in assassinations if state.card_counts[action.target_player] == max_cards])
            
        tax = Action(6, state.active_player)
        if tax in valid_actions and (4 in self.cards):
            return tax
            
        thefts = [action for action in valid_actions if action.type == 5]
        if len(thefts) > 0:
            max_coins = max([state.coins[action.target_player] for action in thefts])
            if max_coins > 0 and (2 in self.cards):
                return random.choice([action for action in thefts if state.coins[action.target_player] == max_coins])
            
        rand = random.random()
        if rand < 0.5:
            income = Action(0, state.active_player)
            if income in valid_actions:
                return income
            
        elif rand < 0.75:
            if tax in valid_actions:
                return tax
            
        elif len(thefts) > 0 and max_coins > 0:
            return random.choice([action for action in thefts if state.coins[action.target_player] == max_coins])
        
        return random.choice(valid_actions)
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        # TODO: add tracking of discarded cards, number of times opponent has taken given action

        if random.random() < 0.2:
            return Challenge(action, self.index, state.active_player)
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
        if random.random() < 0.2:
            return random.choice(valid_actions)
        return None
        
    def choose_card(self, state: State) -> int:

        if 0 in self.cards:
            return self.cards.index(0)
        
        if 3 in self.cards:
            return self.cards.index(3)
        
        if 4 in self.cards:
            return self.cards.index(4)
        
        if 2 in self.cards:
            return self.cards.index(2)
        
        if 1 in self.cards:
            return self.cards.index(1)
        
        return 0


class TrainingPlayer(Player):
    """A player used to train the Deep Q Learning network."""

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        pass
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        pass
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        pass

    def get_policy_action(self, state: torch.tensor) -> torch.tensor:
        pass
        
    def choose_card(self, state: State) -> int:
        pass


class SmartPlayer(Player):
    """A player that follows the policy trained by Deep Q Learning."""

    def get_action(self, state: State, valid_actions: list[Action]) -> Action:
        pass
    
    def get_challenge(self, state: State, action: Action) -> Challenge | None:
        pass
    
    def get_counteraction(self, state: State, valid_actions: list[Action]) -> Action | None:
        pass
        
    def choose_card(self, state: State) -> int:
        pass


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
