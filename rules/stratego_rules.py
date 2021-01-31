from rules.rules import *
from structures.chess_structures import *
from utility.betza import *


class MobileRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.rank == 1 or 2 < piece.rank:
            if wazir(args):
                return [(self.consequence, args)]


class ScoutRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        if piece.rank == 2:
            if rook(game, args):
                return [(self.consequence, args)]


class AttackRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        piece = game.get_board().get_tile(args[0]).get_piece()
        other = game.get_board().get_tile(args[1]).get_piece()

        if other.shape == "0":
            return

        if other.rank == "F":
            return [("move_success", args)]
        elif other.rank == "B":
            if piece.rank == 3:
                return [("move_success", args)]
        else:
            if other.rank == 10:
                if piece.rank == 1:
                    return [("move_success", args)]

            if piece.rank == other.rank:
                return [("take", args[0]), ("take", args[1])]

            if piece.rank > other.rank:
                return [("move_success", args)]

        return [("move_success", (args[1], args[0], *args[2:]))]


class StrategoTouchRule(Rule):
    def __init__(self, consequence: str):
        Rule.__init__(self, watch=["touch"])

        self.prev = None
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):  # args must be a tile identifier corresponding to the board
        if effect == "touch":
            piece = game.get_board().get_tile(args[0]).get_piece()
            player = game.get_turn()

            dropping = any(game.get_board().get_hand(p) for p in "bw")

            if dropping:
                if piece is None:
                    tile, p = args
                    return [("drop", (tile, player))]
            else:
                if game.get_turn() not in args[1]:
                    return

                if self.prev:
                    prev, self.prev = self.prev, None

                    m1, m2 = prev[0], args[0]
                    p = prev[1]
                    return [(self.consequence, (m1, m2, p)), ("select", prev)]
                elif piece:
                    tile, p = args
                    self.prev = (tile, player)
                    return [("select", (tile, player))]


class DropRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["drop", "readstring"])

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
                    return [("create_piece", (tile, player1, drop)), ("dropped", game.get_turn_num())]
