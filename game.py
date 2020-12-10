import tkinter as tk
import numpy as np
import itertools as itr


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itr.zip_longest(*args, fillvalue=fillvalue)


class Game(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self, "game")


class SquareBoardWidget(tk.Canvas):
    def __init__(self, master=None):
        tk.Canvas.__init__(self, master=master)

        self.nx = 8
        self.ny = 8

        self.tiles = np.full((self.nx, self.ny), None, dtype=object)
        self.tags = np.full((self.nx, self.ny), -1, dtype=int)
        self.rules = None

        for ix, v in np.ndenumerate(self.tiles):
            self.tiles[ix] = NormalTile()

        self.redraw()

        self.bind("<Expose>", self.redraw)
        self.bind("<ButtonRelease-1>", self.left_release)

    def set_rules(self, rules):
        self.rules = rules

    def redraw(self, event=None):
        self.delete("all")

        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        for ix, v in np.ndenumerate(self.tiles):
            i, j = ix

            parity = (i + j) % 2
            col = '#E2DA9C' if parity else '#AF8521'

            x, y = i * dx, j * dy
            self.tags[i, j] = self.create_rectangle(x, y, x + dx, y + dy, fill=col)

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

        if self.rules:
            tile_i = self.click_to_tile(event.x, event.y)
            self.rules.process(self, tile_i)


class FreeChess:
    def __init__(self):
        self.touched = None

    def pass_turn(self):
        ...

    def process(self, board: SquareBoardWidget, pos):
        move = self.touch(board, pos)

        if move:
            self.move(*move)

    def touch(self, board: SquareBoardWidget, pos):
        if self.touched:
            pos1 = self.touched
            pos2 = pos
            self.touched = None

            return board, pos1, pos2
        else:
            tile = board.tiles[pos]

            if tile.piece:
                self.touched = pos

            return ()

    def move(self, board, pos1, pos2):
        if pos1 == pos2:
            return

        tile1 = board.tiles[pos1]
        tile2 = board.tiles[pos2]

        tile2.piece = tile1.piece
        tile1.piece = None

        self.pass_turn()

        board.redraw()


class TurnChess(FreeChess):
    def __init__(self):
        FreeChess.__init__(self)

        self.turn = "w"

    def pass_turn(self):
        self.turn = "b" if self.turn == "w" else "w"

    def touch(self, board: SquareBoardWidget, tile_i):
        if self.touched:
            move = FreeChess.touch(self, board, tile_i)
        else:
            tile = board.tiles[tile_i]

            if tile.piece and tile.piece.col == self.turn:
                move = FreeChess.touch(self, board, tile_i)
            else:
                return ()

        return move


class MoveChess(FreeChess):
    def move(self, board, pos1, pos2):
        piece1 = board.tiles[pos1].piece
        s = piece1.shape
        c = piece1.col

        if pos1 == pos2:
            return

        piece2 = board.tiles[pos2].piece

        if piece2 and c == piece2.col:
            return

        dp = np.array(pos2) - np.array(pos1)
        can = False
        if s == "K":
            can = np.all(abs(dp) <= 1)
        elif s == "D":
            can = np.sum(dp != 0) == 1 or abs(dp[0]) == abs(dp[1])
        elif s == "T":
            can = np.sum(dp != 0) == 1
        elif s == "P":
            can = abs(dp[0] * dp[1]) == 2
        elif s == "L":
            can = abs(dp[0]) == abs(dp[1])
        elif s == "p":
            pawn_dp = [0, -1] if c == "w" else [0, 1]

            can = np.all(dp == pawn_dp)

        if can:
            FreeChess.move(self, board, pos1, pos2)


class MoveTurnChess(MoveChess, TurnChess):
    def __init__(self):
        MoveChess.__init__(self)
        TurnChess.__init__(self)

    def process(self, board: SquareBoardWidget, pos):
        move = TurnChess.touch(self, board, pos)
        if move:
            MoveChess.move(self, *move)


class NormalTile:
    def __init__(self):
        self.piece = None


class Piece:
    def __init__(self, shape="A", col="w"):
        self.shape = shape
        self.col = col


class Chess(Game):
    def __init__(self):
        Game.__init__(self)

        self.board = SquareBoardWidget(self)

        self.board.set_rules(MoveTurnChess())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board.grid(sticky="nsew")

    def load_board_str(self, board_str):
        players = board_str.split(";")

        for player in players:
            col = player[0]
            pieces = player[1:]
            pieces = grouper(pieces, 3)

            for x, y, shape in pieces:
                piece = Piece(shape, col)

                i = ord(x) - ord("a")
                j = int(y) - 1

                self.board.tiles[i, j].piece = piece


if __name__ == '__main__':
    chess = Chess()

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")

    chess.mainloop()
