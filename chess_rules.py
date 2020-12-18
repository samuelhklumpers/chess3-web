import json
import random
import threading
import traceback

from chess_structures import MovedPiece
from util import *


class Rule:
    def process(self, game, effect, args):
        ...


class TouchMoveRule(Rule):
    def __init__(self, eout):
        self.prev = None
        self.eout = eout

    def process(self, game, effect, args):
        if effect == "touch":
            piece = game.board.get_tile(args).get_piece()

            if self.prev:
                prev, self.prev = self.prev, None
                return [(self.eout, (prev, args))]
            elif piece:
                self.prev = args

            return []


class IdMoveRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            if args[0] == args[1]:
                return []
            else:
                return [(self.eout, args)]


class MoveTurnRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()

            if piece.get_colour() == game.get_turn():
                return [(self.eout, args)]
            else:
                return []


class MovePlayerRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()

            if piece.get_colour() in game.player:
                return [(self.eout, args)]
            else:
                return []


class FriendlyFireRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            moving_piece = game.board.get_tile(args[0]).get_piece()
            taken_piece = game.board.get_tile(args[1]).get_piece()

            if taken_piece and moving_piece.get_colour() == taken_piece.get_colour():
                return
            else:
                return [(self.eout, args)]


class MoveTakeRule(Rule):
    def __init__(self, ein):
        self.ein = ein

    def process(self, game, effect, args):
        if effect == self.ein:
            moving_piece = game.board.get_tile(args[0]).get_piece()
            taken_piece = game.board.get_tile(args[1]).get_piece()

            moving_id = game.get_id(moving_piece)
            taken_id = game.get_id(taken_piece)
            null_id = game.get_id(None)

            elist = [("set_piece", (args[1], moving_id))]
            elist += [("set_piece", (args[0], null_id))]
            elist += [("moved", (moving_id, args[0], args[1]))]
            elist += [("takes", (moving_id, taken_id, args[0], args[1]))]

            return elist


class TakeRule(Rule):
    def process(self, game, effect, args):
        if effect == "take":
            taken_piece = game.board.get_tile(args).get_piece()
            null_id = game.get_id(None)
            taken_id = game.get_id(taken_piece)
            return [("set_piece", (args, null_id)), ("takes", (null_id, taken_id, args, args))]


class SetPieceRule(Rule):
    def process(self, game, effect, args):
        if effect == "set_piece":
            piece = game.get_from_id(args[1])

            game.board.get_tile(args[0]).set_piece(piece)

            return []


class RedrawRule(Rule):
    def process(self, game, effect, args):
        if effect == "moved":
            game.after_idle(game.board.redraw)


class NextTurnRule(Rule):
    def process(self, game, effect, args):
        if effect == "moved":
            game.turn = "b" if game.turn == "w" else "w"
            game.turn_num += 1


def unpack2ddr(args):
        x1, y1 = args[0]
        x2, y2 = args[1]

        dx, dy = x2 - x1, y2 - y1

        return dx, dy


class AnyRule(Rule):  # warning: ordering side effect
    def __init__(self, rules):
        self.rules = rules

    def process(self, game, effect, args):
        for rule in self.rules:
            elist = rule.process(game, effect, args)

            if elist:
                return elist


class PawnSingleRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == d and not game.board.get_tile(args[1]).get_piece():
                    return [(self.eout, args)]


class PawnDoubleRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == 2 * d and piece.moved == 0 and not game.board.get_tile(args[1]).get_piece():
                    return [(self.eout, args)]


class PawnTakeRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    if game.board.get_tile(args[1]).get_piece():
                        return [(self.eout, args)]


class PawnEnPassantRule(Rule):  # warning: will generate duplicate moves when pawns pass through pieces on a double move
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    x1, y1 = args[0]
                    x3, y3 = x1 + dx, y1

                    other = game.board.get_tile((x3, y3)).get_piece()
                    if other and other.shape == "p" and other.double == game.get_turn_num():
                        return [(self.eout, args), ("take", (x3, y3))]


class KnightRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "P":
                dx, dy = unpack2ddr(args)

                if abs(dx * dy) == 2:
                    return [(self.eout, args)]


class BishopRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "L":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.eout, args)]


class RookRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "T":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.eout, args)]


class QueenRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "D":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 or abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [(self.eout, args)]


class KingRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "K":
                dx, dy = unpack2ddr(args)

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return [(self.eout, args)]


class CastleRule(Rule):
    def __init__(self, ein, eout):
        self.ein = ein
        self.eout = eout

    def process(self, game, effect, args):
        if effect == self.ein:
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

                        return [(self.eout, args), (self.eout, (other, end))]


class MovedRule(Rule):
    def process(self, game, effect, args):
        if effect == "moved":
            piece = game.get_from_id(args[0])

            if isinstance(piece, MovedPiece):
                piece.moved = game.get_turn_num()


class PawnPostDouble(Rule):
    def process(self, game, effect, args):
        if effect == "moved":
            piece = game.get_from_id(args[0])

            if piece.shape == "p":
                dx, dy = unpack2ddr(args[1:])

                if abs(dy) == 2:
                    piece.double = game.get_turn_num()


class WinRule(Rule):
    def process(self, game, effect, args):
        if effect == "takes":
            kings = {}

            for tile in game.board.tiles.flat:
                piece = tile.get_piece()

                if piece and piece.shape == "K":
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


class WinCloseRule(Rule):
    def process(self, game, effect, args):
        if effect == "wins":
            return [("exit", ())]


class ReceiveRule(Rule):
    def run(self, game):
        try:
            roll1 = random.getrandbits(64)
            game.socket.send(roll1.to_bytes(8, "big"))
            data = game.socket.recv(1024)
            roll2 = int.from_bytes(data, "big")

            if roll1 > roll2:
                game.player = "w"
            elif roll2 > roll1:
                game.player = "b"
            else:
                print("you win the lottery (1/2^128)")  # that's pretty impressive
                exit()

            game.receiving = False
            data = game.socket.recv(1024)
            game.receiving = True
            while data:
                for part in data.split(b";")[:-1]:
                    effect, args = json.loads(part.decode())

                    game.ruleset.process(effect, args, prop=False)  # !

                game.receiving = False
                data = game.socket.recv(1024)
                game.receiving = True
        except OSError:
            ...
        except:
            traceback.print_exc()

    def process(self, game, effect, args):
        if effect == "init":
            game.socket_thread = threading.Thread(target=lambda: self.run(game))
            game.socket_thread.start()


class SendRule(Rule):
    def process(self, game, effect, args):
        if not game.receiving:
            game.socket.send(json.dumps((effect, args)).encode() + b";")


class CloseSocket(Rule):
    def process(self, game, effect, args):
        if effect == "exit":
            game.after(1000, lambda: self.close(game))

    def close(self, game):
            try:
                game.socket.shutdown(0)
                game.socket.close()
            except:
                traceback.print_exc()

            if game.socket_thread.is_alive() and game.socket_thread != threading.current_thread():
                print("panic")


class ExitRule(Rule):
    def process(self, game, effect, args):
        if effect == "exit":
            game.after(2000, game.destroy)