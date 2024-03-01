from coup import Coup
from player import GreedyPlayer
from representations import Player


def main():
    game = Coup(2)
    winner = game.play()
    if winner is not None:
        print('This player is the winner:\n')
        print(winner)

if __name__ == '__main__':
    main()