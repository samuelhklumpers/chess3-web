import tkinter as tk
import numpy as np


class Game(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self, "game")


class SquareBoardWidget(tk.Canvas):
    def __init__(self, master=None):
        tk.Canvas.__init__(self, master=master)

        self.nx = 8
        self.ny = 8

        self.board = np.full((self.nx, self.ny), None, dtype=object)
        self.tags = np.full((self.nx, self.ny), -1, dtype=int)
        self.rules = None

        for ix, v in np.ndenumerate(self.board):
            self.board[ix] = NormalTile()

        self.redraw()

        self.bind("<Expose>", self.redraw)
        self.bind("<ButtonRelease-1>", self.left_release)

    def set_rules(self, rules):
        self.rules = rules

    def redraw(self, event=None):
        self.delete("all")

        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        for ix, v in np.ndenumerate(self.board):
            i, j = ix

            parity = (i + j) % 2
            col = '#E2DA9C' if parity else '#AF8521'

            x, y = i * dx, j * dy
            self.tags[i, j] = self.create_rectangle(x, y, x + dx, y + dy, fill=col)

            tile = self.board[ix]

            if tile.piece:
                self.create_text(x + dx/2, y + dy/2, text=tile.piece.shape, fill="black")

    def click_to_tile(self, x, y):
        w, h = self.winfo_width(), self.winfo_height()
        dx, dy = w / self.nx, h / self.ny

        return int(x / dx), int(y / dy)

    def left_release(self, event=None):
        self.create_oval(event.x, event.y, event.x + 2, event.y + 2, fill="red")

        if self.rules:
            tile_i = self.click_to_tile(event.x, event.y)
            self.rules.touch(self, tile_i)


class FreeChess:
    def __init__(self):
        self.touched = None

    def touch(self, board, tile_i):
        if self.touched:
            tile = board.board[tile_i]

            self.move(board, self.touched, tile)
            self.touched = None
        else:
            tile = board.board[tile_i]

            if tile.piece:
                self.touched = tile

    def move(self, board, touch1, touch2):
        if touch1 == touch2:
            return

        touch2.piece = touch1.piece
        touch1.piece = None

        board.redraw()


class NormalTile:
    def __init__(self):
        self.piece = None


class Piece:
    def __init__(self):
        self.shape = "A"


def normal_chess():
    game = Game()
    board = SquareBoardWidget(game)

    board.set_rules(FreeChess())
    board.board[0, 0].piece = Piece()

    game.grid_columnconfigure(0, weight=1)
    game.grid_rowconfigure(0, weight=1)

    board.grid(sticky="nsew")

    game.mainloop()


if __name__ == '__main__':
    normal_chess()
