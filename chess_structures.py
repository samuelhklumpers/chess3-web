import socket
import threading

import numpy as np
import tkinter as tk

from typing import Optional, Callable

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

    def increment(self, colour: str, shape: str, dn: int):
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
            count_svar = tk.StringVar()
            count_svar.set("0")

            count_label = tk.Label(frame, textvariable=count_svar, bg=bg)
            row = len(player)

            icon.grid(row=row, column=0)
            count_label.grid(row=row, column=1)

            counts[shape] = [0, count_svar]

        count_svar = counts[shape][1]
        counts[shape][0] += dn
        count_svar.set(str(counts[shape][0]))
        self.update()


class Piece:
    def __init__(self, shape="A", col="w"):
        self.shape = shape
        self.col = col
        self.double = False

    def get_colour(self):
        return self.col


class NormalTile(Tile):
    def __init__(self):
        self.piece = None

    def get_piece(self):
        return self.piece

    def set_piece(self, piece: Piece):
        ret, self.piece = self.piece, piece
        return ret


class MovedPiece(Piece):
    def __init__(self, shape="A", col="w"):
        Piece.__init__(self, shape=shape, col=col)

        self.moved = 0


class Pawn(MovedPiece):
    def __init__(self, col="w"):
        MovedPiece.__init__(self, shape="p", col=col)

        self.double = False


def parse_boardstr(boardstr: str):
    players = boardstr.split(";")

    pieces = []

    for player in players:
        col = player[0]
        shapes = player[1:]

        for x, y, shape in grouper(shapes, 3):
            i = ord(x) - ord("a")
            j = int(y) - 1
            pos = (i, j)

            pieces += [(pos, col, shape)]

    return pieces


class Chess(Game):
    def __init__(self):
        Game.__init__(self)

        self.board: Optional[Board] = None
        self.counter: Optional[PieceCounter] = None
        self.tkchess: Optional[TkChess] = None

        self.socket: Optional[socket.socket] = None
        self.socket_thread: Optional[threading.Thread] = None

        self.object_map = {0: None}
        self.obj_count = 1

        self.turn = "w"
        self.player = "bw"
        self.turn_num = 1

        self.receiving = True

    def set_ruleset(self, ruleset: Ruleset):
        self.ruleset = ruleset

    def set_board(self, board: "Board"):
        self.board = board

    def set_socket(self, socket: "socket.socket"):
        self.socket = socket

    def get_id(self, item):
        return next(k for k, v in self.object_map.items() if v == item)

    def get_by_id(self, item_id: int):
        return self.object_map[item_id]

    def add_object(self, item):
        tag = self.obj_count
        self.object_map[tag] = item
        self.obj_count += 1
        return tag

    def process(self, effect: str, args):
        if self.ruleset:
            self.ruleset.process(effect, args)

    def get_turn(self):
        return self.turn

    def get_turn_num(self):
        return self.turn_num

    def load_board_str(self, board_str: str):
        for pos, col, shape in parse_boardstr(board_str):
            self.ruleset.process("create_piece", (pos, col, shape))


class TkChess(tk.Tk):
    def __init__(self, chess):
        tk.Tk.__init__(self, "chess")

        self.counter: Optional[PieceCounter] = None

        self.chess = chess
        self.chess.tkchess = self

        self.tkboard = TkBoard(chess.board)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tkboard.grid(column=0, row=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", lambda: chess.ruleset.process("exit", ()))

    def set_counter(self, counter: PieceCounter):
        self.counter = counter
        self.counter.grid(column=1, row=0, sticky="nsew")


class Board:
    def __init__(self, game: Chess):
        self.game = game
        self.tkboard: Optional[TkBoard] = None

        self.nx, self.ny = 8, 8

        self.tiles = np.empty((self.nx, self.ny), dtype=object)

    def make_tiles(self, tile_constr: Callable[[], Tile]):
        for ix, v in np.ndenumerate(self.tiles):
            self.tiles[ix] = tile_constr()

    def click(self, tile_i):
        self.game.process("touch", tile_i)

    def tile_ids(self):
        for (i, j), v in np.ndenumerate(self.tiles):
            yield (i, j)

    def get_piece(self, tile_i):
        return self.get_tile(tile_i).get_piece()

    def get_tile(self, tile_i):
        return self.tiles[tuple(tile_i)]


class TkBoard(tk.Canvas):
    def __init__(self, board: Board, master=None):
        tk.Canvas.__init__(self, master=master)

        self.board: Board = board
        board.tkboard = self

        self.width, self.height = self.winfo_width(), self.winfo_height()
        self.nx, self.ny = board.nx, board.ny

        self.tile_tags = np.full((self.nx, self.ny), -1, dtype=int)
        self.piece_tags = {}

        self.bind("<Configure>", self.resize)
        self.bind("<ButtonRelease-1>", self.left_release)

    def resize(self, event):
        sx, sy = float(event.width) / self.width, float(event.height) / self.height
        self.width, self.height = event.width, event.height
        self.scale("all", 0, 0, sx, sy)

    def draw_tiles(self):
        dx, dy = self.tile_dims()

        for (i, j), v in np.ndenumerate(self.board.tiles):
            x, y = i * dx, j * dy
            parity = (i + j) % 2

            col = HEXCOL["tile_white"] if parity else HEXCOL["tile_brown"]
            self.tile_tags[i, j] = self.create_rectangle(x, y, x + dx, y + dy, fill=col)

    def draw_pieces(self):
        dx, dy = self.tile_dims()

        for (i, j), v in np.ndenumerate(self.board.tiles):
            x, y = i * dx, j * dy

            tile = self.board.tiles[(i, j)]
            piece = tile.piece
            if piece:
                piece_id = self.board.game.get_id(piece)
                tag = self.create_text(x + dx/2, y + dy/2, text=piece.shape)
                self.piece_tags[piece_id] = tag

    def tile_dims(self):
        w, h = self.winfo_width(), self.winfo_height()
        return w / self.nx, h / self.ny

    def click_to_tile(self, x, y):
        dx, dy = self.tile_dims()

        return int(x / dx), int(y / dy)

    def left_release(self, event):
        tile_i = self.click_to_tile(event.x, event.y)
        self.board.click(tile_i)


__all__ = ["PieceCounter", "NormalTile", "Piece", "MovedPiece", "Pawn", "Chess", "TkChess", "Board", "TkBoard"]