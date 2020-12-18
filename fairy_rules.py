import json
import random
import threading
import traceback

from chess_structures import MovedPiece
from chess_rules import Rule
from util import *


def unpack2ddr(args):
        x1, y1 = args[0]
        x2, y2 = args[1]

        dx, dy = x2 - x1, y2 - y1

        return dx, dy


class FighterRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "F":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) <= 1 and dy == d and game.board.get_tile(args[1]).get_piece():
                    return [(self.eout, args)]

                if dx == 0 and dy == 2 * d and not game.board.get_tile(args[1]).get_piece():
                    return [(self.eout, args)]


class RiderRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "R":
                dx, dy = unpack2ddr(args)

                if abs(dx * dy) == 2 or abs(dx * dy) == 8:
                    return [(self.eout, args)]


class KirinRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "C":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) + abs(dy) == 2:
                    return [(self.eout, args)]


class SniperRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "S":
                x1, y1 = args[0]
                x2, y2 = args[1]

                moving_id = game.get_id(piece)

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    if game.board.get_tile((x2, y2)):
                        return [("take", (x2, y2)), ("moved", (moving_id, args[0], args[0]))]

                if max(abs(dx), abs(dy)) == 1:
                    return [(self.eout, args)]


class SquareRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "]":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if max(abs(dx), abs(dy)) <= 3:
                    return [(self.eout, args)]


class MasterRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "M":
                dx, dy = unpack2ddr(args)

                if abs(dx) <= 1 and abs(dy) <= 1 or (dy == 0 and abs(dx) == 3):
                    return [(self.eout, args)]


class FairyWinRule(Rule):
    def process(self, game, effect, args):
        if effect == "takes":
            kings = {}

            for tile in game.board.tiles.flat:
                piece = tile.get_piece()

                if piece and piece.shape == "M":
                    kings.setdefault(piece.get_colour(), 0)
                    kings[piece.get_colour()] += 1

            alive = [col for col in kings if kings[col] > 0]
            n_alive = len(alive)

            if n_alive > 1:
                ...
            elif n_alive == 1:
                return [("wins", alive[0])]
            else:
                return [("wins", None)]