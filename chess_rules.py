import datetime
import json
import random
import traceback
import threading

from typing import List

from rules import *
from structures import *
from chess_structures import *


class TouchMoveRule(Rule):
    def __init__(self, consequence: str):
        self.prev = None
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):  # args must be a tile identifier corresponding to the board
        if effect == "touch":
            piece = game.board.get_tile(args).get_piece()

            if self.prev:
                prev, self.prev = self.prev, None
                return [(self.consequence, (prev, args)), ("select", prev)]
            elif piece:
                self.prev = args
                return [("select", args)]

            return []


class IdMoveRule(Rule):
    def __init__(self, cause: str, consequence: str):
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
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()

            if piece:  # how does this become None?
                if piece.get_colour() == game.get_turn():
                    return [(self.consequence, args)]
                else:
                    return []


class MovePlayerRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            piece = game.board.get_tile(args[0]).get_piece()

            if piece.get_colour() in game.player:
                return [(self.consequence, args)]
            else:
                return []


class FriendlyFireRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            moving_piece = game.board.get_tile(args[0]).get_piece()
            taken_piece = game.board.get_tile(args[1]).get_piece()

            if taken_piece and moving_piece.get_colour() == taken_piece.get_colour():
                return
            else:
                return [(self.consequence, args)]


class SuccesfulMoveRule(Rule):
    def __init__(self, cause: str):
        self.cause = cause

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            return [("move_success", args)]


class MoveTakeRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "move_success":
            moving_piece = game.board.get_tile(args[0]).get_piece()
            taken_piece = game.board.get_tile(args[1]).get_piece()

            moving_id = game.get_id(moving_piece)
            taken_id = game.get_id(taken_piece)
            null_id = game.get_id(None)

            elist = []

            if args[0] != args[1]:
                elist += [("set_piece", (args[1], moving_id))]
                elist += [("set_piece", (args[0], null_id))]
                elist += [("takes", (moving_id, taken_id, args[0], args[1]))]
            elist += [("moved", (moving_id, args[0], args[1]))]

            return elist


class TakeRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "take":
            taken_piece = game.board.get_tile(args).get_piece()
            null_id = game.get_id(None)
            taken_id = game.get_id(taken_piece)
            return [("set_piece", (args, null_id)), ("takes", (null_id, taken_id, args, args))]


class CreatePieceRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "create_piece":
            pos, col, shape = args

            if shape in "KT":
                piece = MovedPiece(shape, col)
            elif shape in "p":
                piece = Pawn(col)
            else:
                piece = Piece(shape, col)

            piece_id = game.add_object(piece)

            return [("set_piece", (pos, piece_id))]


class SetPieceRule(Rule):
    def process(self, game: Chess, effect: str, args):  # args must be a tuple of (tile identifier, object identifier)
        if effect == "set_piece":
            piece = game.get_from_id(args[1])

            game.board.get_tile(args[0]).set_piece(piece)

            return [("piece_set", args)]


class MoveRedrawRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            return [("redraw", ())]


class NextTurnRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            game.turn = "b" if game.turn == "w" else "w"
            game.turn_num += 1

            return [("turn_changed", ())]


class AnyRule(Rule):  # warning: ordering side effect
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def process(self, game, effect, args):
        for rule in self.rules:
            elist = rule.process(game, effect, args)

            if elist:
                return elist


class MovedRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece = game.get_from_id(args[0])

            if isinstance(piece, MovedPiece):
                piece.moved = game.get_turn_num()


class CounterRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "takes":
            taken_id = args[1]
            piece = game.get_from_id(taken_id)

            if piece:
                col, shape = piece.get_colour(), piece.shape

                game.counter.increment(col, shape, -1)
        elif effect == "create_piece":
            _, col, shape = args
            game.counter.increment(col, shape, 1)


class WinRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "takes":
            kings = {}

            for tile in game.board.tiles.flat:
                piece = tile.get_piece()

                if piece and piece.shape == "K":
                    kings.setdefault(piece.get_colour(), 0)
                    kings[piece.get_colour()] += 1

            alive = [col for col in kings if kings[col] > 0]
            n_alive = len(alive)

            if n_alive == 1:
                print(alive[0], "wins")
                return [("wins", alive[0])]
            elif n_alive == 0:
                print("draw")
                return [("wins", None)]


class WinCloseRule(Rule):
    def process(self, game: Game, effect: str, args):
        if effect == "wins":
            return [("exit", ())]


class SetPlayerRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "set_player":
            game.player = args

            print("you are playing as:", args)


class RecordRule(Rule):
    def __init__(self):
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


class ReceiveRule(Rule):
    def run(self, game: Chess):
        try:
            roll1 = random.getrandbits(64)
            game.socket.send(roll1.to_bytes(8, "big"))
            data = game.socket.recv(1024)
            roll2 = int.from_bytes(data, "big")

            if roll1 > roll2:
                player = "w"
            elif roll2 > roll1:
                player = "b"
            else:
                print("you win the lottery (1/2^128)")  # that's pretty impressive
                return

            game.receiving = True
            game.ruleset.process("set_player", player)
            game.receiving = False
            data = game.socket.recv(1024)
            game.receiving = True
            while data:
                for part in data.split(b";")[:-1]:
                    effect, args = json.loads(part.decode())

                    game.ruleset.process(effect, args)

                game.receiving = False
                data = game.socket.recv(1024)
                game.receiving = True
        except OSError:
            ...
        except:
            traceback.print_exc()

    def process(self, game: Chess, effect: str, args):
        if effect == "init":
            game.socket_thread = threading.Thread(target=lambda: self.run(game))
            game.socket_thread.start()


class SendRule(Rule):
    def __init__(self, whitelist: List[Rule]):
        self.whitelist = whitelist

    def process(self, game: Chess, effect: str, args):
        if not game.receiving:
            if effect in self.whitelist:
                game.socket.send(json.dumps((effect, args)).encode() + b";")


class CloseSocket(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "exit":
            game.tkchess.after(1000, lambda: self.close(game))

    def close(self, game: Chess):
            try:
                game.socket.shutdown(0)
                game.socket.close()
            except:
                traceback.print_exc()

            if game.socket_thread.is_alive() and game.socket_thread != threading.current_thread():
                print("panic")


class ExitRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "exit":
            print("exiting")
            game.tkchess.after(2000, game.tkchess.destroy)


__all__ = ['TouchMoveRule', 'IdMoveRule', 'MoveTurnRule', 'MovePlayerRule', 'FriendlyFireRule', 'SuccesfulMoveRule',
           'MoveTakeRule', 'TakeRule', 'CreatePieceRule', 'SetPieceRule', 'MoveRedrawRule', 'NextTurnRule', 'AnyRule',
           'MovedRule', 'CounterRule', 'WinRule', 'WinCloseRule', 'SetPlayerRule', 'ReceiveRule', 'SendRule', 'CloseSocket',
           'RecordRule', 'PlaybackRule', 'ExitRule']
