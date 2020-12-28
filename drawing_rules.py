import os

import numpy as np

from PIL import Image
from PIL import ImageTk

from chess_structures import *
from rules import *


def fill_opaque(arr, col):
    if len(col) == 3:
        col = [*col, 255]

    out = arr.copy()
    out[out[..., -1] != 0] = col
    return out


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


class DrawInitRule(Rule):
    def process(self, game: Chess, effect, args):
        if effect == "init":
            return [("redraw", ())]


class RedrawRule(Rule):
    def process(self, game: Chess, effect, args):
        if effect == "redraw":
            board = game.board
            board.delete("all")
            board.draw_tiles()

            draw_list = []
            for ix, v in np.ndenumerate(board.tiles):
                draw_list += [("draw_piece", (ix, None)), ("mark_cmap", (ix, "normal"))]

            return draw_list


class SelectRule(Rule):
    def __init__(self):
        self.selected = None

    def process(self, game: Chess, effect, args):
        if effect == "select":
            ret = []

            if self.selected:
                ret += [("mark_cmap", (args, "normal"))]

            if args != self.selected:
                self.selected = args
                ret += [("mark_cmap", (args, "#FF0000"))]
            else:
                self.selected = None

            return ret


class DrawPieceRule(Rule):
    def __init__(self):
        self.folder = "images"
        self.files = {"K": "king.png", "D": "queen.png", "T": "rook.png",
                      "L": "bishop.png", "P": "knight.png", "p": "pawn.png"}
        self.bitmaps = {}
        self.images = {}

        self.refs = []  # Q: How do I create a memory leak? A: Like this.

    def process(self, game: Chess, effect, args):
        if effect == "init":
            for shape in self.files:
                fn = os.path.join(self.folder, self.files[shape])
                im = Image.open(fn)
                im = im.resize((60, 60))
                self.images[shape] = ImageTk.PhotoImage(im)
                self.bitmaps[shape] = np.array(im)
        elif effect == "draw_piece":
            pos, col = args

            board = game.board
            piece = board.get_tile(pos).get_piece()

            if piece:
                i, j = pos
                w, h = board.winfo_width(), board.winfo_height()
                dx, dy = w / board.nx, h / board.ny
                x, y = i * dx, j * dy

                shape = piece.shape

                piece_id = game.get_id(piece)

                if shape in self.images:
                    if col is not None:
                        arr = self.bitmaps[shape]
                        arr = fill_opaque(arr, col)
                        im = Image.fromarray(arr)
                        self.refs += [im]
                        rep = ImageTk.PhotoImage(im)
                        self.refs += [rep]
                        tag = board.create_image(x + dx/2, y + dy/2, image=rep)
                    else:
                        rep = self.images[shape]
                        tag = board.create_image(x + dx/2, y + dy/2, image=rep)
                else:
                    rep = shape
                    tag = board.create_text(x + dx/2, y + dy/2, text=rep)

                board.piece_tags[piece_id] = tag


class MarkCMAPRule(Rule):
    cmap = {"w": "#FFFFFF", "b": "#000000"}

    def process(self, game: Chess, effect, args):
        if effect == "mark_cmap":
            pos, col = args

            piece = game.board.get_tile(pos).get_piece()

            if col != "normal":
                return [("mark", args)]

            if piece:
                pc = piece.get_colour()
                col = self.cmap[pc]

                return [("mark", (pos, col))]


class MarkRule(Rule):
    def process(self, game: Chess, effect, args):
        if effect == "mark":
            pos, col = args

            board = game.board
            piece = board.get_tile(pos).get_piece()

            if piece:
                piece_id = game.get_id(piece)
                tag = board.piece_tags[piece_id]

                if board.type(tag) == "image":
                    bitcol = hex_to_rgb(col)
                    return [("draw_piece", (pos, bitcol))]
                elif board.type(tag) == "text":
                    board.itemconfig(tag, fill=col)


__all__ = ['DrawInitRule', 'RedrawRule', 'SelectRule', 'fill_opaque', 'DrawPieceRule', 'MarkCMAPRule', 'hex_to_rgb', 'MarkRule']
