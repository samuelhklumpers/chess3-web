import json
import random
import socket
import threading
import time
import tkinter as tk
import traceback
from tkinter import simpledialog

import numpy as np
import itertools as itr


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itr.zip_longest(*args, fillvalue=fillvalue)


def xyiter(x1, y1, x2, y2, incl_start=False, incl_end=False):
    sx = np.sign(x2 - x1)
    sy = np.sign(y2 - y1)

    if incl_start:
        yield x1, y1

    x1 += sx
    y1 += sy

    while not (sx != 0 and x1 == x2) and not (sy != 0 and y1 == y2):
        yield x1, y1

        x1 += sx
        y1 += sy

    if incl_end:
        yield x2, y2


class Game(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self, "game")


class SquareBoardWidget(tk.Canvas):
    def __init__(self, game, master=None):
        tk.Canvas.__init__(self, master=master)

        self.nx, self.ny = 8, 8

        self.game = game
        self.tiles = np.full((self.nx, self.ny), None, dtype=object)

        for ix, v in np.ndenumerate(self.tiles):
            self.tiles[ix] = NormalTile()

        self.redraw()  # remove this and move to normal drawing rule

        self.bind("<Expose>", self.redraw)
        self.bind("<ButtonRelease-1>", self.left_release)

    def redraw(self, event=None):
        self.delete("all")

        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        for ix, v in np.ndenumerate(self.tiles):
            i, j = ix
            x, y = i * dx, j * dy
            parity = (i + j) % 2

            col = '#E2DA9C' if parity else '#AF8521'
            self.create_rectangle(x, y, x + dx, y + dy, fill=col)

            tile = self.tiles[ix]
            if tile.piece:
                col = "white" if tile.piece.col == "w" else "black"
                self.create_text(x + dx/2, y + dy/2, text=tile.piece.shape, fill=col)

    def click_to_tile(self, x, y):
        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        return int(x / dx), int(y / dy)

    def left_release(self, event=None):
        self.create_oval(event.x, event.y, event.x + 2, event.y + 2, fill="red")

        tile_i = self.click_to_tile(event.x, event.y)
        self.game.process("touch", tile_i)

    def get_tile(self, tile_i):
        return self.tiles[tuple(tile_i)]


class Ruleset:
    def __init__(self, game):
        self.game = game
        self.rules = {}
        self.lock = threading.RLock()

        self.debug = True

    def add_rule(self, rule, prio=1):
        # 0 forbidden/debug
        # -1 forbidden/debug
        self.rules.setdefault(prio, []).append(rule)

    def process_all(self, elist):
        try:
            for effect, args in elist:
                self.process(effect, args)
        except ValueError as e:
            print(elist)
            raise e

    def process_no_prop(self, effect, args):
        if self.debug:
            print(effect, args)

        keys = list(self.rules.keys())

        early = [k for k in keys if k >= 0]
        late = [k for k in keys if k < 0]

        early.sort()
        late.sort()

        # make corecursive
        for k in early:
            for rule in self.rules[k]:
                rule.process(self.game, effect, args)
        for k in late:
            for rule in self.rules[k]:
                rule.process(self.game, effect, args)

    def process(self, effect, args):
        with self.lock:
            self._process(effect, args)

    def _process(self, effect, args):
        if self.debug:
            print(effect, args)

        keys = list(self.rules.keys())

        early = [k for k in keys if k >= 0]
        late = [k for k in keys if k < 0]

        early.sort()
        late.sort()

        # make corecursive
        for k in early:
            elist = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    elist += res

            self.process_all(elist)

        for k in late:
            elist = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    elist += res

            self.process_all(elist)


class Rule:
    def process(self, game, effect, args):
        ...


class TouchMoveRule(Rule):
    def __init__(self):
        self.prev = None

    def process(self, game, effect, args):
        if effect == "touch":
            piece = game.board.get_tile(args).get_piece()

            if self.prev:
                prev, self.prev = self.prev, None
                return [("move1", (prev, args))]
            elif piece:
                self.prev = args

            return []


class IdMoveRule(Rule):
    def process(self, game, effect, args):
        if effect == "move1":
            if args[0] == args[1]:
                return []
            else:
                return [("move2", args)]


class MoveTurnRule(Rule):
    def process(self, game, effect, args):
        if effect == "move2":
            piece = game.board.get_tile(args[0]).get_piece()

            if piece.get_colour() == game.get_turn():
                return [("move21", args)]
            else:
                return []


class MovePlayerRule(Rule):
    def process(self, game, effect, args):
        if effect == "move21":
            piece = game.board.get_tile(args[0]).get_piece()

            if piece.get_colour() in game.player:
                return [("move3", args)]
            else:
                return []


class FriendlyFireRule(Rule):
    def process(self, game, effect, args):
        if effect == "move4":
            moving_piece = game.board.get_tile(args[0]).get_piece()
            taken_piece = game.board.get_tile(args[1]).get_piece()

            if taken_piece and moving_piece.get_colour() == taken_piece.get_colour():
                return
            else:
                return [("move5", args)]


class MoveTakeRule(Rule):
    def process(self, game, effect, args):
        if effect == "move5":
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
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == d and not game.board.get_tile(args[1]).get_piece():
                    return [("move4", args)]


class PawnDoubleRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if dx == 0 and dy == 2 * d and piece.moved == 0 and not game.board.get_tile(args[1]).get_piece():
                    return [("move4", args)]


class PawnTakeRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    if game.board.get_tile(args[1]).get_piece():
                        return [("move4", args)]


class PawnEnPassantRule(Rule):  # warning: will generate duplicate moves when pawns pass through pieces on a double move
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                dx, dy = unpack2ddr(args)

                d = -1 if piece.get_colour() == "w" else 1

                if abs(dx) == 1 and dy == d:
                    x1, y1 = args[0]
                    x3, y3 = x1 + dx, y1

                    other = game.board.get_tile((x3, y3)).get_piece()
                    if other and other.shape == "p" and other.double == game.get_turn_num():
                        return [("move4", args), ("take", (x3, y3))]


class KnightRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "P":
                dx, dy = unpack2ddr(args)

                if abs(dx * dy) == 2:
                    return [("move4", args)]


class BishopRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "L":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [("move4", args)]


class RookRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "T":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0:
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [("move4", args)]


class QueenRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "D":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if dx * dy == 0 or abs(dx) == abs(dy):
                    for x, y in xyiter(x1, y1, x2, y2):
                        if game.board.get_tile((x, y)).get_piece():
                            return

                    return [("move4", args)]


class KingRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "K":
                dx, dy = unpack2ddr(args)

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return [("move4", args)]


class CastleRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
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

                        return [("move4", args), ("move4", (other, end))]


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
                print("you win the lottery (1/2^128)")
                exit()


            game.receiving = False
            data = game.socket.recv(1024)
            game.receiving = True
            while data:
                effect, args = json.loads(data.decode())

                game.ruleset.process_no_prop(effect, args)  # !

                game.receiving = False
                data = game.socket.recv(1024)
                game.receiving = True
        except:
            traceback.print_exc()

    def process(self, game, effect, args):
        if effect == "init":
            game.socket_thread = threading.Thread(target=lambda: self.run(game))
            game.socket_thread.start()


class SendRule(Rule):
    def process(self, game, effect, args):
        if not game.receiving:
            game.socket.send(json.dumps((effect, args)).encode())


class NormalTile:
    def __init__(self):
        self.piece = None

    def get_piece(self):
        return self.piece

    def set_piece(self, piece):
        ret = self.piece
        self.piece = piece
        return ret


class Piece:
    def __init__(self, shape="A", col="w"):
        self.shape = shape
        self.col = col
        self.double = False

    def get_colour(self):
        return self.col


class MovedPiece(Piece):
    def __init__(self, shape="A", col="w"):
        Piece.__init__(self, shape=shape, col=col)

        self.moved = 0


class Pawn(MovedPiece):
    def __init__(self, col="w"):
        MovedPiece.__init__(self, shape="p", col=col)

        self.double = False


class Chess(Game):
    def __init__(self):
        Game.__init__(self)

        self.ruleset = None
        self.object_map = {0: None}
        self.obj_count = 1
        self.board = SquareBoardWidget(self)
        self.turn = "w"
        self.player = "bw"
        self.turn_num = 1

        self.socket = None
        self.socket_thread = None
        self.receiving = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board.grid(sticky="nsew")

    def set_ruleset(self, ruleset):
        self.ruleset = ruleset

    def set_socket(self, socket):
        self.socket = socket

    def get_id(self, item):
        return next(k for k, v in self.object_map.items() if v == item)

    def get_from_id(self, item_id):
        return self.object_map[item_id]

    def add_object(self, item):
        self.object_map[self.obj_count] = item
        self.obj_count += 1

    def process(self, effect, args):
        if self.ruleset:
            self.ruleset.process(effect, args)

    def get_turn(self):
        return self.turn

    def get_turn_num(self):
        return self.turn_num

    def load_board_str(self, board_str):
        players = board_str.split(";")

        for player in players:
            col = player[0]
            pieces = player[1:]
            pieces = grouper(pieces, 3)

            for x, y, shape in pieces:
                if shape in "KT":
                    piece = MovedPiece(shape, col)
                elif shape in "p":
                    piece = Pawn(col)
                else:
                    piece = Piece(shape, col)

                i = ord(x) - ord("a")
                j = int(y) - 1

                self.board.tiles[i, j].piece = piece
                self.add_object(piece)


class OnlineDialog(simpledialog.Dialog):
    def __init__(self, parent):
        simpledialog.Dialog.__init__(self, title="Online Chess", parent=parent)

    def body(self, master):
        self.raddr = tk.StringVar()
        self.lport = tk.StringVar()
        self.rport = tk.StringVar()
        self.active = tk.BooleanVar()

        addr_label = tk.Label(master, text="Address:", justify=tk.LEFT)
        addr_entry = tk.Entry(master, textvariable=self.raddr)

        local_label = tk.Label(master, text="Local port (empty defaults to remote port):", justify=tk.LEFT)
        local_entry = tk.Entry(master, textvariable=self.lport)

        remote_label = tk.Label(master, text="Remote port:", justify=tk.LEFT)
        remote_entry = tk.Entry(master, textvariable=self.rport)

        active_label = tk.Label(master, text="Active:", justify=tk.LEFT)
        active_tickbox = tk.Checkbutton(master, variable=self.active)

        addr_label.grid(row=0, column=0)
        addr_entry.grid(row=0, column=1)

        local_label.grid(row=1, column=0)
        local_entry.grid(row=1, column=1)

        remote_label.grid(row=2, column=0)
        remote_entry.grid(row=2, column=1)

        active_label.grid(row=3, column=0)
        active_tickbox.grid(row=3, column=1)

        return addr_entry

    def validate(self):
        addr, lport, rport, active = self.raddr.get(), self.lport.get(), self.rport.get(), self.active.get()
        lport = int(lport) if lport else rport
        rport = int(rport) if rport else rport

        self.result = addr, lport, rport, active
        print(self.result)
        return True


def make_socket(remote_address, remote_port, local_port=None, active=True):
    if not local_port:
        local_port = remote_port

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", local_port))

    def listen(s, ret):
        print("listening")
        s.listen(0)
        s, a = s.accept()
        print("accepted", a)

        ret.append((s, a))

    if active:
        print("trying to connect", (remote_address, remote_port))

        while True:
            try:
                s.connect((remote_address, remote_port))
                break
            except:
                traceback.print_exc()
                print("retrying")
                time.sleep(10)
    else:
        ret = []

        t = threading.Thread(target=lambda: listen(s, ret))
        t.start()

        try:
            while t.is_alive():
                t.join(1)
            s, a = ret[0]
        except:
            s.close()
            t.join()
            print("stopping listening")
            return

    print("connected")

    return s


def play_chess():
    chess = Chess()

    dialog = OnlineDialog(chess)
    addr, lport, rport, active = dialog.result

    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)
    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")

    ruleset = Ruleset(chess)
    ruleset.add_rule(TouchMoveRule())
    ruleset.add_rule(IdMoveRule())
    ruleset.add_rule(MoveTurnRule())
    ruleset.add_rule(MovePlayerRule())
    ruleset.add_rule(TakeRule())
    ruleset.add_rule(MoveTakeRule())
    ruleset.add_rule(FriendlyFireRule())
    ruleset.add_rule(SetPieceRule())
    ruleset.add_rule(RedrawRule())
    ruleset.add_rule(NextTurnRule())

    pawn_rule = AnyRule([PawnSingleRule(), PawnDoubleRule(), PawnTakeRule(), PawnEnPassantRule()])

    ruleset.add_rule(pawn_rule)
    ruleset.add_rule(KnightRule())
    ruleset.add_rule(BishopRule())
    ruleset.add_rule(RookRule())
    ruleset.add_rule(QueenRule())
    ruleset.add_rule(KingRule())

    ruleset.add_rule(CastleRule())

    ruleset.add_rule(MovedRule())
    ruleset.add_rule(PawnPostDouble())

    ruleset.add_rule(WinRule())

    ruleset.add_rule(ReceiveRule())
    ruleset.add_rule(SendRule())

    chess.set_ruleset(ruleset)
    ruleset.process("init", ())

    chess.board.redraw()

    chess.mainloop()


if __name__ == '__main__':
    play_chess()