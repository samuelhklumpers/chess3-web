import numpy as np

from rules.rules import *
from structures.chess_structures import *
from utility.util import *


class FerzRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "F":
                dx, dy = unpack2ddr(args)

                if abs(dx) == abs(dy) == 1:
                    return [(self.consequence, args)]


class JumperRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()

            if piece.shape == "J":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1
                dx2, dy2 = np.sign(dx), np.sign(dy)

                if game.get_board().get_tile(args[1]).get_piece():
                    return

                if dx * dy == 0 or abs(dx) == abs(dy):
                    d = max(abs(dx), abs(dy))

                    x3, y3 = x1 + dx2, y1 + dy2
                    piece2 = game.get_board().get_tile((x3, y3)).get_piece()

                    if d == 2:
                        if piece2 and piece.get_colour() != piece2.get_colour():
                            return [(self.consequence, args), ("take", (x3, y3))]
                        else:
                            return [(self.consequence, args)]
                    elif d == 3:
                        x4, y4 = x1 + dx2 * 2, y1 + dy2 * 2
                        piece3 = game.get_board().get_tile((x4, y4)).get_piece()

                        if piece2:
                            if piece.get_colour() == piece2.get_colour():
                                if piece3:
                                    if piece.get_colour() == piece3.get_colour():
                                        return [(self.consequence, args)]
                                    else:
                                        return [(self.consequence, args), ("take", (x4, y4))]
                                else:
                                    return [(self.consequence, args)]
                        else:
                            if piece3 and piece.get_colour() != piece3.get_colour():
                                return [(self.consequence, args), ("take", (x4, y4))]
                            else:
                                return [(self.consequence, args)]


class KirinRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "C":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) + abs(dy) == 2:
                    return [(self.consequence, args)]


class ShooterRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "S":
                col = piece.get_colour()

                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if max(abs(dx), abs(dy)) == 1:
                    if not game.get_board().get_tile((x2, y2)).get_piece():
                        if dx * dy == 0:
                            x3 = x1 + 4 * dx
                            y3 = y1 + 4 * dy
                            shoot = None

                            for x, y in xyiter(x1, y1, x3, y3, incl_end=True):
                                tile = game.get_board().get_tile((x, y))
                                if tile and tile.get_piece():
                                    shoot = (x, y)
                                    break

                            if shoot and game.get_board().get_tile(shoot).get_piece().get_colour() != col:
                                return [("take", shoot), (self.consequence, args)]
                            elif not shoot:
                                return [(self.consequence, args)]

                        else:
                            return [(self.consequence, args)]


class WheelRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "W":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 and abs(dx + dy) < 4:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.get_board().get_tile((x, y)).get_piece():
                            return
                    return [(self.consequence, args)]

                if abs(dx * dy) == 2:
                    return [(self.consequence, args)]


__all__ = ['FerzRule', 'JumperRule', 'KirinRule', 'ShooterRule', 'WheelRule']
