import threading

import tkinter as tk
import numpy as np


class Game(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self, "game")

        self.ruleset = Ruleset(self)


class Tile:
    ...


class Board(tk.Canvas):
    def __init__(self, game: Game, master=None, tiles=Tile):
        tk.Canvas.__init__(self, master=master)

        self.game = game

        self.width, self.height = self.winfo_width(), self.winfo_height()
        self.nx, self.ny = 8, 8

        self.tiles = np.empty((self.nx, self.ny), dtype=object)

        self.tile_tags = np.full((self.nx, self.ny), -1, dtype=int)
        self.piece_tags = {}

        for ix, v in np.ndenumerate(self.tiles):
            self.tiles[ix] = tiles()

        self.bind("<Configure>", self.resize)
        self.bind("<ButtonRelease-1>", self.left_release)

    def resize(self, event):
        sx, sy = float(event.width) / self.width, float(event.height) / self.height
        self.width, self.height = event.width, event.height
        self.scale("all", 0, 0, sx, sy)

    def draw_tiles(self):
        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        for (i, j), v in np.ndenumerate(self.tiles):
            x, y = i * dx, j * dy
            parity = (i + j) % 2

            col = '#E2DA9C' if parity else '#AF8521'
            self.tile_tags[i, j] = self.create_rectangle(x, y, x + dx, y + dy, fill=col)

    def draw_pieces(self):
        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        for (i, j), v in np.ndenumerate(self.tiles):
            x, y = i * dx, j * dy

            tile = self.tiles[(i, j)]
            piece = tile.piece
            if piece:
                piece_id = self.game.get_id(piece)
                tag = self.create_text(x + dx/2, y + dy/2, text=piece.shape)
                self.piece_tags[piece_id] = tag

    def tile_dims(self):
        w, h = self.winfo_width(), self.winfo_height()
        return w / self.nx, h / self.ny

    def click_to_tile(self, x, y):
        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        return int(x / dx), int(y / dy)

    def left_release(self, event=None):
        tile_i = self.click_to_tile(event.x, event.y)
        self.game.process("touch", tile_i)

    def tile_ids(self):
        for (i, j), v in np.ndenumerate(self.tiles):
            yield (i, j)

    def get_piece(self, tile_i):
        return self.get_tile(tile_i).get_piece()

    def get_tile(self, tile_i):
        return self.tiles[tuple(tile_i)]


class Ruleset:
    def __init__(self, game: Game):
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
            consequences = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    consequences += res

            if prop:
                self.process_all(consequences)

        for k in late:
            consequences = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    consequences += res

            if prop:
                self.process_all(consequences)


__all__ = ["Game", "Tile", "Board", "Ruleset"]