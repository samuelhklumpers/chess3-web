from structures.chess_structures import *


class StrategoPiece(Piece):
    def __init__(self, col, rank):
        Piece.__init__(self, "@", col)

        self.rank = rank
