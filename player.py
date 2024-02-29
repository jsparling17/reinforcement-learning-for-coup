from representations import Action, Challenge, State


class Player:
    def __init__(self, index: int = 0, cards: list[int] = [0, 0], coins: int = 2, name: str = 'Bot', is_bot: bool = True, agent = None):
        self.index: int = index
        self.cards: list[int] = cards
        self.discarded_cards: list[int] = []
        self.coins: int = coins
        self.name: str = name
        self.is_bot: bool = is_bot
        self.agent = agent

    def get_action(self, state: State, valid_actions: list[Action]):
        #TODO if agent, use agent to select action

        #TODO Is not bot action
        
        pass

    def get_challenge(self, state, active_player, action, target_player):
        state = [self.name] + state
        if target_player != -1 and not(target_player is None):
            valid_actions = [[active_player.name, action, target_player.name, i] for i in range(2)]
        else:
            valid_actions = [[active_player.name, action, -1, i] for i in range(2)]
        _, is_challenge = self.agent.act(state, valid_actions)
        return is_challenge

    def lose_card(self):
        # TODO Decides what card to lose and loses it
        card_pos = 0
        card = self.cards[card_pos]
        del self.cards[card_pos]
        return card

    def fake_lose_card(self, state, card):
        state = [self.name] + state
        valid_actions = [[-1, card, -1, i] for i in range(2)]
        _, is_challenge = self.agent.act(state, valid_actions)
        return is_challenge

    def choose_cards(self, state):
        # TODO 
        index1, index2 = 0, 1

        card1 = self.cards[index1]
        card2 = self.cards[index2]

        del self.cards[index1]
        del self.cards[index2]

        return [card1, card2]

    def show_card(self, card):
        if self.cards[0] == card:
            del self.cards[0]
        else:
            del self.cards[1]
        