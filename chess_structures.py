import tkinter as tk

from structures import Tile, Board, Game
from util import grouper


class PieceCounter(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master=master)

        self.cmap = {"w": "white", "b": "black"}
        self.players = {}
        self.frames = {}
        self.counts = {}

    def increment(self, colour, shape, dn):
        WEIRD_GREEN = "#00FF99"

        if colour not in self.players:
            self.players[colour] = {}
            self.counts[colour] = {}
            self.frames[colour] = frame = tk.Frame(self, bg=WEIRD_GREEN)
            frame.pack(fill=tk.BOTH, expand=1)
        player = self.players[colour]
        counts = self.counts[colour]
        frame = self.frames[colour]

        if shape not in player:
            player[shape] = 0

            col = self.cmap[colour]

            icon = tk.Label(frame, text=shape, bg=WEIRD_GREEN, fg=col)
            count = tk.StringVar()
            count.set("0")

            count_label = tk.Label(frame, textvariable=count, bg=WEIRD_GREEN)
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
        self.board = Board(game=self, master=self, tiles=NormalTile)
        self.counter = PieceCounter(self)
        self.turn = "w"
        self.player = "bw"
        self.turn_num = 1

        self.socket = None
        self.socket_thread = None
        self.receiving = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board.grid(column=0, row=0, sticky="nsew")
        self.counter.grid(column=1, row=0, sticky="nsew")

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


__all__ = ["PieceCounter", "NormalTile", "Piece", "MovedPiece", "Pawn", "Chess"]