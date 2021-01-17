from structures.chess_structures import *


class ShogiBoard(Board):
    def __init__(self, game):
        Board.__init__(self, game, 9, 9)

        self.hands = {}

    def get_hand(self, colour):
        return self.hands.setdefault(colour, [])
