import datetime
import json

from typing import Dict, Callable

from rules.rules import *
from structures.structures import *
from structures.chess_structures import *


class TouchMoveRule(Rule):
    def __init__(self, consequence: str, cause: str = "touch"):
        Rule.__init__(self, watch=[cause])

        self.prev = None
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):  # args must be a tile identifier corresponding to the board
        if effect == self.cause:
            if game.get_turn() not in args[1]:
                return

            piece = game.get_board().get_tile(args[0]).get_piece()

            if self.prev:
                prev, self.prev = self.prev, None

                m1, m2 = prev[0], args[0]
                p = prev[1]
                return [("select", prev), (self.consequence, (m1, m2, p))]
            elif piece:
                self.prev = args
                return [("select", args)]

            return []


class IdMoveRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):  # args must be a tuple of (two) tile identifiers
        if effect == self.cause:
            if args[0] == args[1]:
                return []
            else:
                return [(self.consequence, args)]


class MoveTurnRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()

            if piece:  # how does this become None?
                if piece.get_colour() == game.get_turn():
                    return [(self.consequence, args)]
                else:
                    return []


class MovePlayerRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.get_board().get_tile(args[0]).get_piece()

            if piece.get_colour() in args[2]:
                return [(self.consequence, args)]
            else:
                return []


class FriendlyFireRule(Rule):
    def __init__(self, cause: str, consequence: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            moving_piece = game.get_board().get_tile(args[0]).get_piece()
            taken_piece = game.get_board().get_tile(args[1]).get_piece()

            if taken_piece and moving_piece.get_colour() == taken_piece.get_colour():
                return
            else:
                return [(self.consequence, args)]


class SuccesfulMoveRule(Rule):
    def __init__(self, cause: str):
        Rule.__init__(self, watch=[cause])

        self.cause = cause

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            return [("move_success", args)]


class MoveTakeRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["move_success"])

    def process(self, game: Chess, effect: str, args):
        if effect == "move_success":
            moving_piece = game.get_board().get_tile(args[0]).get_piece()
            taken_piece = game.get_board().get_tile(args[1]).get_piece()

            moving_id = game.get_id(moving_piece)
            taken_id = game.get_id(taken_piece)
            null_id = game.get_id(None)

            elist = []

            print(args[0], args[1])

            if args[0] != args[1]:
                elist += [("set_piece", (args[1], moving_id))]
                elist += [("set_piece", (args[0], null_id))]
                elist += [("takes", (moving_id, taken_id, args[0], args[1]))]
            elist += [("moved", (moving_id, args[0], args[1]))]

            return elist


class TakeRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["take"])

    def process(self, game: Chess, effect: str, args):
        if effect == "take":
            taken_piece = game.get_board().get_tile(args).get_piece()
            null_id = game.get_id(None)
            taken_id = game.get_id(taken_piece)
            return [("set_piece", (args, null_id)), ("takes", (null_id, taken_id, args, args))]


class CreatePieceRule(Rule):
    def __init__(self, constructors: Dict[str, Callable[[str, str], Piece]]):
        Rule.__init__(self, watch=["create_piece"])

        self.constrs = constructors

    def process(self, game: Chess, effect: str, args):
        if effect == "create_piece":
            pos, col, shape = args

            constr = self.constrs.get(shape, Piece)
            piece = constr(shape, col)

            piece_id = game.add_object(piece)

            return [("set_piece", (pos, piece_id))]


class SetPieceRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["set_piece"])

    def process(self, game: Chess, effect: str, args):  # args must be a tuple of (tile identifier, object identifier)
        if effect == "set_piece":
            piece = game.get_by_id(args[1])

            game.get_board().get_tile(args[0]).set_piece(piece)

            return [("piece_set", args)]


class MoveRedrawRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved"])

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            return [("redraw", ())]


class NextTurnRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved", "do_turn"])

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            return [("do_turn", ())]

        if effect == "do_turn":
            if game.turn == "w":
                game.turn = "b"
            elif game.turn == "b":
                game.turn = "w"

            game.turn_num += 1

            return [("turn_changed", game.turn)]


class MovedRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved"])

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece = game.get_by_id(args[0])

            if isinstance(piece, MovedPiece):
                piece.moved = game.get_turn_num()


class CounterRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["takes", "create_piece"])

    def process(self, game: Chess, effect: str, args):
        if effect == "takes":
            taken_id = args[1]
            piece = game.get_by_id(taken_id)

            if piece:
                col, shape = piece.get_colour(), piece.shape

                game.tkchess.counter.increment(col, shape, -1)
        elif effect == "create_piece":
            _, col, shape = args
            game.tkchess.counter.increment(col, shape, 1)


class WinRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["takes"])

    def process(self, game: Chess, effect: str, args):
        if effect == "takes":
            kings = {}

            for tile_id in game.get_board().tile_ids():
                tile = game.get_board().get_tile(tile_id)
                piece = tile.get_piece()

                if piece and piece.shape == "K":
                    kings.setdefault(piece.get_colour(), 0)
                    kings[piece.get_colour()] += 1

            alive = [col for col in kings if kings[col] > 0]
            n_alive = len(alive)

            if n_alive == 1:
                return [("wins", alive[0])]
            elif n_alive == 0:
                return [("wins", None)]


class WinMessageRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["wins"])

    def process(self, game: Chess, effect: str, args):
        if effect == "wins":
            print("wins", args)


class WinCloseRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["wins"])

    def process(self, game: Game, effect: str, args):
        if effect == "wins":
            return [("exit", ())]


class SetPlayerRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["set_player"])

    def process(self, game: Chess, effect: str, args):
        if effect == "set_player":
            game.player = args

            print("you are playing as:", args)


class RecordRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["moved", "exit"])

        self.start = datetime.datetime.now()
        self.log = []

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece_id, start, end = args

            self.log += [(start, end)]
        elif effect == "exit":
            fn = self.start.strftime("%Y_%m_%d_%H_%M_%S.chs")

            with open(fn, mode="w") as f:
                json.dump(self.log, f)


class PlaybackRule(Rule):
    def __init__(self, game: Chess, fn: str, move0: str):
        Rule.__init__(self)

        game.tkchess.bind("<Return>", self.step)

        self.move0 = move0
        self.ruleset = game.ruleset
        self.i = 0

        with open(fn, mode="r") as f:
            self.log = json.load(f)

    def step(self, event=None):
        if self.i == len(self.log):
            return

        move = self.log[self.i]
        self.i += 1

        self.ruleset.process(self.move0, move)

    def process(self, game: Game, effect: str, args):
        ...


class ExitRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["exit"])

    def process(self, game: Chess, effect: str, args):
        if effect == "exit":
            print("exiting")
            game.tkchess.after(2000, game.tkchess.destroy)


__all__ = ['TouchMoveRule', 'IdMoveRule', 'MoveTurnRule', 'MovePlayerRule', 'FriendlyFireRule', 'SuccesfulMoveRule',
           'MoveTakeRule', 'TakeRule', 'CreatePieceRule', 'SetPieceRule', 'MoveRedrawRule', 'NextTurnRule',
           'MovedRule', 'CounterRule', 'WinRule', 'WinMessageRule', 'WinCloseRule', 'SetPlayerRule', 'RecordRule',
           'PlaybackRule', 'ExitRule']
