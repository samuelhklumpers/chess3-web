import threading

import tkinter as tk
import numpy as np

from util import grouper


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

    def add_all(self, rules, prio=1):
        for rule in rules:
            self.add_rule(rule, prio=prio)

    def process_all(self, elist, prop=True):
        try:
            for effect, args in elist:
                self.process(effect, args, prop=prop)
        except ValueError as e:
            raise e

    def process(self, effect, args, prop=True):
        with self.lock:
            self._process(effect, args, prop=prop)

    def _process(self, effect, args, prop=True):
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

            if prop:
                self.process_all(elist)

        for k in late:
            elist = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    elist += res

            if prop:
                self.process_all(elist)


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

        self.protocol("WM_DELETE_WINDOW", lambda: self.ruleset.process("exit", ()))

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