import numpy as np
import tkinter as tk

from structures import *
from util import *
from colours import *


class PieceCounter(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master=master)

        self.cmap = HEXCOL.copy()
        self.players = {}
        self.frames = {}
        self.counts = {}

    def increment(self, colour, shape, dn):
        bg = HEXCOL["counter_bg"]

        if colour not in self.players:
            self.players[colour] = {}
            self.counts[colour] = {}
            self.frames[colour] = frame = tk.Frame(self, bg=bg)
            frame.pack(fill=tk.BOTH, expand=1)
        player = self.players[colour]
        counts = self.counts[colour]
        frame = self.frames[colour]

        if shape not in player:
            player[shape] = 0

            col = self.cmap[colour]

            icon = tk.Label(frame, text=shape, bg=bg, fg=col)
            count = tk.StringVar()
            count.set("0")

            count_label = tk.Label(frame, textvariable=count, bg=bg)
            row = len(player)

            icon.grid(row=row, column=0)
            count_label.grid(row=row, column=1)

            counts[shape] = [0, count]

        var = counts[shape][1]
        counts[shape][0] += dn
        var.set(str(counts[shape][0]))
        self.update()


class NormalTile(Tile):
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

        self.object_map = {0: None}
        self.obj_count = 1
        self.turn = "w"
        self.player = "bw"
        self.turn_num = 1

        self.board = None
        self.counter = None

        self.socket = None
        self.socket_thread = None
        self.receiving = True

        self.tkchess = None

    def set_ruleset(self, ruleset):
        self.ruleset = ruleset

    def set_socket(self, socket):
        self.socket = socket

    def get_id(self, item):
        return next(k for k, v in self.object_map.items() if v == item)

    def get_from_id(self, item_id):
        return self.object_map[item_id]

    def add_object(self, item):
        tag = self.obj_count
        self.object_map[tag] = item
        self.obj_count += 1
        return tag

    def process(self, effect, args):
        if self.ruleset:
            self.ruleset.process(effect, args)

    def get_turn(self):
        return self.turn

    def get_turn_num(self):
        return self.turn_num

    def load_board_str(self, board_str):
        players = board_str.split(";")

        create = []
        for player in players:
            col = player[0]
            pieces = player[1:]
            pieces = grouper(pieces, 3)

            for x, y, shape in pieces:
                i = ord(x) - ord("a")
                j = int(y) - 1

                pos = (i, j)

                create += [("create_piece", (pos, col, shape))]
        self.ruleset.process_all(create)


class TkChess(tk.Tk):
    def __init__(self, chess):
        tk.Tk.__init__(self, "chess")

        self.chess = chess
        self.chess.tkchess = self

        chess.board = Board(game=chess, master=self, tiles=NormalTile)
        chess.counter = PieceCounter(master=self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        chess.board.grid(column=0, row=0, sticky="nsew")
        chess.counter.grid(column=1, row=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", lambda: chess.ruleset.process("exit", ()))


class Board(tk.Canvas):
    def __init__(self, game: Chess, master=None, tiles=Tile):
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


__all__ = ["PieceCounter", "NormalTile", "Piece", "MovedPiece", "Pawn", "Chess", "TkChess", "Board"]