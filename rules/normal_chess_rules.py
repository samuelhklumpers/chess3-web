from tkinter import simpledialog
from typing import List

from structures.lazy_structures import RefChess
from rules.rules import *
from structures.chess_structures import *
from structures.structures import Ruleset
from util.util import *


class PawnSingleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == d and not game.get_board().get_tile(args[1]).get_piece():
                    return [(self.consequence, args)]


class PawnDoubleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "p":
                x, y = args[0]
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                mid = (x, y + d)

                if dx == 0 and dy == 2 * d and piece.moved == 0:
                    if not game.get_board().get_tile(mid).get_piece():
                        if not game.get_board().get_tile(args[1]).get_piece():
                            return [(self.consequence, args)]


class PawnTakeRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    if game.get_board().get_tile(args[1]).get_piece():
                        return [(self.consequence, args)]


class PawnEnPassantRule(Rule):  # warning: will generate duplicate moves when pawns pass through pieces on a double move
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1
                if abs(dx) == 1 and dy == d:
                    x1, y1 = args[0]
                    x3, y3 = x1 + dx, y1

                    other = game.get_board().get_tile((x3, y3)).get_piece()
                    if other and other.shape == "p" and other.double == game.get_turn_num():
                        return [(self.consequence, args), ("take", (x3, y3))]


class KnightRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "P":
                dx, dy = unpack2ddr(args)

                if abs(dx * dy) == 2:
                    return [(self.consequence, args)]


class BishopRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "L":
                x1, y1 = args[0]
                x2, y2 = args[1]
                dx, dy = x2 - x1, y2 - y1

                if abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.get_board().get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class RookRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "T":
                x1, y1 = args[0]
                x2, y2 = args[1]
                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.get_board().get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class QueenRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "D":
                x1, y1 = args[0]
                x2, y2 = args[1]
                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 or abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.get_board().get_tile((x, y)).get_piece():
                            return

                    return [(self.consequence, args)]


class KingRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
            if piece.shape == "K":
                dx, dy = unpack2ddr(args)

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return [(self.consequence, args)]


class CastleRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()
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
                        rook = game.get_board().get_tile(other).get_piece()
                    else:
                        other = (x1 + 3, y1)
                        end = (x1 + 1, y1)
                        rook = game.get_board().get_tile(other).get_piece()

                    if rook and rook.moved == 0:
                        # minor hack because making two moves screws up parity
                        return [("moved", ()), (self.consequence, args), (self.consequence, (other, end))]


class PawnPostDouble(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved"])

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece = game.get_by_id(args[0])

            if piece.shape == "p":
                dx, dy = unpack2ddr(args[1:])

                if abs(dy) == 2:
                    piece.double = game.get_turn_num()


class PromoteRule(Rule):
    def __init__(self, eligible: List[str], promotions: List[str]):
        Rule.__init__(self, watch=["moved"])

        self.eligible = eligible
        self.promotions = promotions

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            board = game.get_board()
            piece_id, start, end = args
            piece = game.get_by_id(piece_id)
            shape = piece.shape
            col = piece.get_colour()

            if col not in game.get_player():
                return

            y = 0 if col == "w" else board.ny - 1

            if end[1] == y:
                if shape in self.eligible:
                    promotion = simpledialog.askstring("Promotion", "One of: " + str(self.promotions))

                    elist = []
                    elist += [("take", end)]
                    # avoid this ^ and skip to cleanup when using exploding pieces or so
                    if promotion in self.promotions:
                        elist += [("create_piece", (end, col, promotion))]
                    return elist


class CheckRule(Rule):
    def __init__(self, cause: str, consequence: str, move0: str, lazy_set: Ruleset):
        Rule.__init__(self, watch=[cause])

        self.move0 = move0
        self.cause = cause
        self.consequence = consequence
        self.lazy_set = lazy_set

        self.valid_indicator = IndicatorRule(["move_success"])
        self.win_indicator = IndicatorRule(["wins"])
        self.lazy_set.add_rule(self.valid_indicator)
        self.lazy_set.add_rule(self.win_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            self.valid_indicator.unset()
            self.win_indicator.unset()

            you = game.get_turn()

            ref = RefChess(game)

            self.lazy_set.game = ref
            self.lazy_set.process(effect, args)

            if not self.valid_indicator.is_set():
                return []

            win = self.win_indicator.is_set()

            if win and win != you:  # did we commit suicide?
                return []

            double_ref = RefChess(ref)
            self.lazy_set.game = double_ref
            for tile_id in game.get_board().tile_ids():
                for target_id in game.get_board().tile_ids():
                    self.win_indicator.unset()

                    self.lazy_set.process(self.move0, (tile_id, target_id))

                    win = self.win_indicator.is_set()
                    if win and win != you:  # would you lose next turn?
                        return []

                    double_ref = RefChess(ref)
                    self.lazy_set.game = double_ref

            return [(self.consequence, args)]


class CheckMateRule(Rule):
    def process(self, game: Chess, effect: str, args):
        ...


__all__ = ['PawnSingleRule', 'PawnDoubleRule', 'PawnTakeRule', 'PawnEnPassantRule', 'KnightRule', 'BishopRule',
           'RookRule', 'QueenRule', 'KingRule', 'CastleRule', 'PawnPostDouble', 'PromoteRule', "CheckRule"]