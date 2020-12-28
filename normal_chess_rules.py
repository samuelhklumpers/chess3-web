from rules import *
from chess_structures import *
from util import *


class PawnSingleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == d and not game.board.get_tile(args[1]).get_piece():
                    return [(self.consequence, args)]


class PawnDoubleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == 2 * d and piece.moved == 0 and not game.board.get_tile(args[1]).get_piece():
                    return [(self.consequence, args)]


class PawnTakeRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    if game.board.get_tile(args[1]).get_piece():
                        return [(self.consequence, args)]


class PawnEnPassantRule(Rule):  # warning: will generate duplicate moves when pawns pass through pieces on a double move
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    x1, y1 = args[0]
                    x3, y3 = x1 + dx, y1

                    other = game.board.get_tile((x3, y3)).get_piece()
                    if other and other.shape == "p" and other.double == game.get_turn_num():
                        return [(self.consequence, args), ("take", (x3, y3))]


class KnightRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "P":
                dx, dy = unpack2ddr(args)

                if abs(dx * dy) == 2:
                    return [(self.consequence, args)]


class BishopRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "L":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class RookRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "T":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class QueenRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "D":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 or abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class KingRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "K":
                dx, dy = unpack2ddr(args)

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return [(self.consequence, args)]


class CastleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "K":
                if piece.moved > 0:
                    return

                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) == 2 and dy <= 0:
                    if dx < 0:
                        other = (x1 - 4, y1)
                        end = (x1 - 1, y1)
                        rook = game.board.get_tile(other).get_piece()
                    else:
                        other = (x1 + 3, y1)
                        end = (x1 + 1, y1)
                        rook = game.board.get_tile(other).get_piece()

                    if rook and rook.moved == 0:
                        game.turn = "b" if game.turn == "w" else "w"
                        game.turn_num -= 1 # minor hack because making two moves screws up parity

                        return [(self.consequence, args), (self.consequence, (other, end))]


class PawnPostDouble(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece = game.get_from_id(args[0])

            if piece.shape == "p":
                dx, dy = unpack2ddr(args[1:])

                if abs(dy) == 2:
                    piece.double = game.get_turn_num()


__all__ = ['PawnSingleRule', 'PawnDoubleRule', 'PawnTakeRule', 'PawnEnPassantRule', 'KnightRule', 'BishopRule',
           'RookRule', 'QueenRule', 'KingRule', 'CastleRule', 'PawnPostDouble']