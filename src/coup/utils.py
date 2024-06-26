from coup.representations import Action, Counter, Player
import random

# maps action number representation to name of action; i.e. ACTION_NAMES[i] gives the name of the action represented by i
ACTION_NAMES: list[str] = ['Income', 'Foreign Aid', 'Tax', 'Exchange', 'Steal', 'Assassinate', 'Coup']

# maps action names to associated indices
ACTION_INDICES: dict[str, int] = {'Income' : 0, 'Foreign Aid' : 1, 'Tax' : 2, 'Exchange' : 3, 'Steal' : 4, 'Assassinate' : 5, 'Coup' : 6}

# maps card number representation to name of card; i.e. CARD_NAMES[i] gives the name of the card represented by i
CARD_NAMES: list[str] = ['Ambassador', 'Assassin', 'Captain', 'Contessa', 'Duke']

# maps card names to associated indices
CARD_INDICES: dict[str, int] = {'Ambassador' : 0, 'Assassin' : 1, 'Captain' : 2, 'Contessa' : 3, 'Duke' : 4}

# maps action number representation to associated card
ACTION_IDX_CARD: dict[int, int] = {2 : 4, 3 : 0, 4 : 2, 5 : 1}

# maps action number representation to card that blocks it
ACTION_IDX_BLOCKER: dict[int, list[int]] = {1 : [4], 4 : [0, 2], 5 : [3]}

def generate_valid_actions(current_player: Player, players: list[Player], player_coins: dict[str, int], player_cards: dict[str, list[int]]) -> list[Action]:
    """
    Return all possible actions of the form (p1, p2, type) where

    p1 = current player
    p2 = any other player that is still alive
    type = the type of action 
    """
    p1 = current_player.name
    other_players = [p2.name for p2 in players if p2.name != p1 and len(player_cards[p2.name]) > 0]

    possible_actions = []

    if player_coins[p1] >= 10:
        return [Action(p1, p2, 6) for p2 in other_players]
    if player_coins[p1] >= 3:
        possible_actions += [Action(p1, p2, 5) for p2 in other_players]
    if player_coins[p1] >= 7:
        possible_actions += [Action(p1, p2, 6) for p2 in other_players]
    
    possible_actions += [Action(p1, p1, 0), Action(p1, p1, 1), Action(p1, p1, 2), Action(p1, p1, 3)]

    possible_actions += [Action(p1, p2.name, 4) for p2 in players if p2.name != p1 and player_coins[p2.name] > 0]

    return possible_actions

def generate_valid_counters(player_name: str, action: Action) -> list[Counter]:
    """
    Return all possible counters of the form (player_name, attempted, challenge, counter_1) where

    player_name = player
    attempted = boolean whether player chose to block
    challenge = True if player challenges, or False if player claims a role to block
    counter_1 = True if counter is against action, False if against other counter
    """

    counter_1 = (action.type >= 0)

    possible_counters = [Counter(player_name, False, False, counter_1)]

    if action.type in [1, 4, 5]:
        possible_counters += [Counter(player_name, True, False, True)]

    if action.type in [2, 3, 4, 5, -1]:
        possible_counters += [Counter(player_name, True, True, counter_1)]

    return possible_counters

def action_bluffed(action_type: int, active_cards: list[int]) -> bool:
    return not ACTION_IDX_CARD[action_type] in active_cards

def counter_1_bluffed(action_type: int, counter_cards: list[int]) -> bool:
    return not bool(set(ACTION_IDX_BLOCKER[action_type]).intersection(set(counter_cards)))

def income(player_name: str, player_coins: dict[str, int]) -> None:
    player_coins[player_name] += 1

def foreign_aid(player_name: str, player_coins: dict[str, int]) -> None:
    player_coins[player_name] += 2

def tax(player_name: str, player_coins: dict[str, int]) -> None:
    player_coins[player_name] += 3

def steal(player1_name: str, player2_name: str, player_coins: dict[str, int]) -> None:
    player_coins[player1_name] += min(player_coins[player2_name], 2)
    player_coins[player2_name] -= min(player_coins[player2_name], 2)

def coup(player1_name: str, player2_name: str, player_coins: dict[str, int], player_cards: dict[str, list[int]], card_idx: int, player_discards: dict[str, list[int]]) -> None:
    player_coins[player1_name] -= 7
    if len(player_cards[player2_name]) < 2: card_idx = 0
    lost_card = player_cards[player2_name].pop(card_idx)
    player_discards[player2_name].append(lost_card)

def assassinate(player1_name: str, player2_name: str, player_coins: dict[str, int], player_cards: dict[str, list[int]], card_idx: int, player_discards: dict[str, list[int]]) -> None:
    player_coins[player1_name] -= 3
    if len(player_cards[player2_name]) < 2: card_idx = 0
    lost_card = player_cards[player2_name].pop(card_idx)
    player_discards[player2_name].append(lost_card)

def lose_challenge(player_name: str, player_cards: dict[str, list[int]], card_idx: int, player_discards: dict[str, list[int]]) -> None:
    if len(player_cards[player_name]) < 2: card_idx = 0
    lost_card = player_cards[player_name].pop(card_idx)
    player_discards[player_name].append(lost_card)

def exchange(player_name: str, player_cards: dict[str, list[int]], cards: list[int], cards_idxs: list[int], deck: list[int]) -> None:
    discards = [cards[idx] for idx in cards_idxs]
    for idx in cards_idxs:
        cards[idx] = None
    player_cards[player_name] = [c for c in cards if c != None]
    deck += discards
    random.shuffle(deck)