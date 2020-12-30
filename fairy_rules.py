from chess_rules import Rule
from util import *


def unpack2ddr(args):
        x1, y1 = args[0]
        x2, y2 = args[1]

        dx, dy = x2 - x1, y2 - y1

        return dx, dy


class FerzRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "F":
                dx, dy = unpack2ddr(args)

                if abs(dx) == abs(dy) == 1:
                    return [(self.eout, args)]


class JumperRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "J":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if game.board.get_tile(args[1]).get_piece():
                    return

                if (dx * dy == 0 or abs(dx) == abs(dy)) and max(abs(dx), abs(dy)) == 2:
                    x3, y3 = x1 + dx // 2, y1 + dy // 2

                    piece2 = game.board.get_tile((x3, y3)).get_piece()

                    elist = [(self.eout, args)]

                    if piece2 and piece.get_colour() != piece2.get_colour():
                        elist += [("take", (x3, y3))]

                    return elist


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


class ShooterRule(Rule):
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

                if dx * dy == 0 and abs(dx + dy) < 5:
                    can_fire = True
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            can_fire = False

                    if can_fire and game.board.get_tile((x2, y2)).get_piece():
                        return [("take", (x2, y2)), (self.eout, (args[0], args[0]))]

                if max(abs(dx), abs(dy)) == 1:
                    if not game.board.get_tile((x2, y2)).get_piece():
                        return [(self.eout, args)]


class WheelRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "W":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 and abs(dx + dy) < 4:
                    return [(self.eout, args)]

                if abs(dx * dy) == 2:
                    return [(self.eout, args)]


__all__ = ['FerzRule', 'JumperRule', 'KirinRule', 'ShooterRule', 'WheelRule']
