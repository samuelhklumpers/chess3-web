import numpy as np

from rules.rules import *
from structures.chess_structures import *
from utility.util import *


# betza lol
def forward(game: Chess, args):
    dx, dy = unpack2ddr(args)
    c = game.get_board().get_tile(args[0]).get_piece().get_colour()
    d = 1 if c == "b" else -1

    if np.sign(dy) == d:
        return args


def wazir(args):
    dx, dy = unpack2ddr(args)

    if abs(dx) + abs(dy) == 1:
        return args


def ferz(args):
    dx, dy = unpack2ddr(args)

    if abs(dx * dy) == 1:
        return args


def rook(game: Chess, args):
    x1, y1 = args[0]
    x2, y2 = args[1]
    dx, dy = unpack2ddr(args)

    b = game.get_board()

    if dx * dy == 0 and not any(b.get_tile(x).get_piece() for x in xyiter(x1, y1, x2, y2)):
        return args


def bishop(game: Chess, args):
    x1, y1 = args[0]
    x2, y2 = args[1]
    dx, dy = unpack2ddr(args)

    b = game.get_board()

    if abs(dx) == abs(dy) and not any(b.get_tile(x).get_piece() for x in xyiter(x1, y1, x2, y2)):
        return args


def knight(args):
    dx, dy = unpack2ddr(args)

    if abs(dx * dy) == 2:
        return args


def gold(game, args):
    return wazir(args) or (forward(game, args) and ferz(args))


class SRookRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "R":
            if rook(game, args):
                return [(self.consequence, args)]


class DragonRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "D":
            if ferz(args) or rook(game, args):
                return [(self.consequence, args)]


class SBishopRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "B":
            if bishop(game, args):
                return [(self.consequence, args)]


class HorseRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "H":
            if wazir(args) or bishop(game, args):
                return [(self.consequence, args)]


class GoldRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "G":
            if gold(game, args):
                return [(self.consequence, args)]


class SilverRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "S":
            if ferz(args) or (forward(game, args) and wazir(args)):
                return [(self.consequence, args)]


class PromotedSilverRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "+S":
            if gold(game, args):
                return [(self.consequence, args)]


class CassiaRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "N":
            if forward(game, args) and knight(args):
                return [(self.consequence, args)]


class PromotedCassiaRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "+N":
            if gold(game, args):
                return [(self.consequence, args)]


class Lance(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "L":
            if forward(game, args) and rook(game, args):
                return [(self.consequence, args)]


class PromotedLanceRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "+L":
            if gold(game, args):
                return [(self.consequence, args)]


class SoldierRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "P":
            if wazir(args) and forward(game, args):
                return [(self.consequence, args)]


class PromotedSoldierRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.shape == "+P":
            if gold(game, args):
                return [(self.consequence, args)]


class ShogiPromoteStartRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved"])

        self.promotion = {"R": "+R", "B": "+B", "S": "+S", "N": "+N", "L": "+L", "P": "+P"}

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece_id, start, end = args

            piece = game.get_by_id(piece_id)
            shape = piece.shape

            if shape not in self.promotion:
                return

            col = piece.get_colour()

            if col not in game.get_player():
                return

            board = game.get_board()

            y = end[1]
            ymax = board.ny
            if col == "w":
                can = y < 3
                must = (shape in ["P", "L", "N"] and y == 0) or (shape == "N" and y == 1)
            else:
                can = y > ymax - 3
                must = (shape in ["P", "L", "N"] and y == ymax - 1) or (shape == "N" and y == ymax - 2)

            if must:
                return [("promote", (end, col, self.promotion[shape]))]

            if can:
                return [("lock_turn", ()), ("promoting", (end, col)),
                        ("askstring", ("Promote [Y/N]?", col))]


class ShogiPromoteReadRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["promote", "promoting", "readstring"])

        self.promotion = {"R": "+R", "B": "+B", "S": "+S", "N": "+N", "L": "+L", "P": "+P"}
        self.promoting = None

    def process(self, game: Chess, effect: str, args):
        if effect == "promoting":
            self.promoting = args
        elif effect == "promote":
            end, col, res = args
            null_id = game.get_id(None)
            return [("set_piece", (end, null_id)), ("create_piece", (end, col, res))]
        elif effect == "readstring":
            if self.promoting:
                text, player = args
                end, col = self.promoting
                shape = game.get_board().get_tile(end).get_piece().shape

                if not player == col:
                    return [("askstring", ("Promote [Y/N]?", col))]

                if text.lower() == "y":
                    self.promoting = None
                    return [("promote", (end, col, self.promotion[shape])), ("unlock_turn", ())]
                elif text.lower() != "n":
                    return [("askstring", ("Promote [Y/N]?", col))]


class ShogiTakeRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["takes"])

        self.promotion = {"R": "+R", "B": "+B", "S": "+S", "N": "+N", "L": "+L", "P": "+P"}
        self.demotion = {v: k for (k, v) in self.promotion.items()}

    def process(self, game: Chess, effect: str, args):
        moving_id, taken_id, _, _ = args
        moving = game.get_by_id(moving_id)
        taken = game.get_by_id(taken_id)

        shape = taken.shape
        shape = self.demotion.get(shape, shape)

        return [("capture", (moving.get_colour(), shape))]


class CaptureRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["capture"])

    def process(self, game: Chess, effect: str, args):
        colour, shape = args
        game.get_board().get_hand(colour).add(shape)


class ShogiTouchRule(Rule):
    def __init__(self, consequence: str):
        Rule.__init__(self, watch=["touch"])

        self.prev = None
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):  # args must be a tile identifier corresponding to the board
        if effect == "touch":
            if game.get_turn() not in args[1]:
                return
            player = game.get_turn()

            piece = game.get_board().get_tile(args[0]).get_piece()

            if self.prev:
                prev, self.prev = self.prev, None

                m1, m2 = prev[0], args[0]
                p = prev[1]
                return [(self.consequence, (m1, m2, p)), ("select", prev)]
            elif piece:
                tile, p = args
                self.prev = (tile, player)
                return [("select", (tile, player))]
            else:
                tile, p = args
                return [("drop", (tile, player))]


class DropRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["drop"])

        self.dropping = False

    def process(self, game: Chess, effect: str, args):
        if effect == "drop":
            tile, player = args

            hand = game.get_board().get_hand(player)

            if hand:
                unique = list(set(hand))
                self.dropping = (tile, player)

                return [("askstring", ("Drop? (one of:) " + ", ".join(unique), player))]
        elif effect == "readstring":
            if self.dropping:
                drop, player1 = args
                tile, player2 = self.dropping

                if not player1 == player2:
                    return

                hand = game.get_board().get_hand(player1)
                self.dropping = False

                if drop in hand:
                    return [("create_piece", tile, player1, drop)]
