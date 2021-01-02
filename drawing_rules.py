import os

import numpy as np

from PIL import Image
from PIL import ImageTk

from chess_structures import *
from rules import *
from structures import Ruleset


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
                draw_list += [("draw_piece", ix)]

            return draw_list


class SelectRule(Rule):
    def __init__(self):
        self.selected = None

    def process(self, game: Chess, effect, args):
        if effect == "select":
            ret = []

            if self.selected:
                ret += [("mark_cmap", (args, "normal")), ("unselected", self.selected)]

            if args != self.selected:
                self.selected = args
                ret += [("mark_cmap", (args, "#FF0000")), ("selected" , args)]
            else:
                self.selected = None

            return ret


class IndicatorRule(Rule):
    def __init__(self, watch):
        self.triggered = False
        self.watch = watch

    def set(self):
        self.triggered = True

    def unset(self):
        self.triggered = False

    def is_set(self):
        return self.triggered

    def process(self, game: Chess, effect: str, args):
        if effect in self.watch:
            self.set()


def search(self, game: Chess, around):  # around must be tile_id
    self.success_indicator.unset()
    for tile_id in game.board.tile_ids():
        self.subruleset.process(self.move0, (around, tile_id))

        if self.success_indicator.is_set():
            yield tile_id

        self.success_indicator.unset()


class MarkValidRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        self.subruleset = subruleset
        self.move0 = move0

        self.tags = []

        self.success_indicator = IndicatorRule(["move_success"])

        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == "selected":
            valid = list(search(self, game, around=args))

            dx, dy = game.board.tile_dims()
            for i, j in valid:
                x, y = i * dx, j * dy

                self.tags += [game.board.create_text(x+dx/2, y+dy/2, text="x", fill="red")]
        elif effect == "unselected":
            for tag in self.tags:
                game.board.delete(tag)
            self.tags = []


class DrawSetPieceRule(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "piece_set":
            pos, piece_id = args

            piece = game.get_from_id(piece_id)

            shape = piece.shape if piece else ""
            col = piece.get_colour() if piece else ""

            return [("draw_piece_at_cmap", (pos, shape, col))]


class DrawPieceCMAPRule(Rule):
    cmap = {"w": "#FFFFFF", "b": "#000000"}

    def process(self, game: Chess, effect, args):
        if effect == "draw_piece_at_cmap":
            pos, shape, col = args

            if col in self.cmap:
                col = self.cmap[col]

            return [("draw_piece_at", (pos, shape, col))]


class DrawPieceRule(Rule):  # parametrize
    def __init__(self):
        self.folder = "images"
        self.files = {"K": "king.png", "D": "queen.png", "T": "rook.png",
                      "L": "bishop.png", "P": "knight.png", "p": "pawn.png",
                      "F": "ferz.png", "J": "jumper.png", "C": "kirin.png",
                      "S": "shooter.png", "W": "wheel.png"}
        self.bitmaps = {}
        self.images = {}
        self.photos = {}

        self.copies = {}  # by tile

    def load_shape(self, shape):
        if shape in self.photos and "" in self.photos[shape]:
            return self.photos[shape][""], self.bitmaps[shape][""]
        else:
            fn = os.path.join(self.folder, self.files[shape])
            im = Image.open(fn)
            im = im.resize((60, 60))
            photo = ImageTk.PhotoImage(im)
            self.photos.setdefault(shape, {}).setdefault("", photo)
            self.images.setdefault(shape, {}).setdefault("", im)
            arr = np.array(im)
            self.bitmaps.setdefault(shape, {}).setdefault("", arr)

            return photo, arr

    def load_colour(self, shape, col):
        if shape in self.photos and col in self.photos[shape]:
            return self.photos[shape][col]
        else:
            _, arr = self.load_shape(shape)
            col = hex_to_rgb(col)
            arr = fill_opaque(arr, col)
            im = Image.fromarray(arr)
            photo = ImageTk.PhotoImage(im)

            self.photos[shape][col] = photo
            self.images[shape][col] = im
            self.bitmaps[shape][col] = arr

            return photo, im

    def draw_image(self, game, pos, shape, col):
        self.undraw(game, pos)

        board = game.board
        i, j = pos
        w, h = board.winfo_width(), board.winfo_height()
        dx, dy = w / board.nx, h / board.ny
        x, y = i * dx, j * dy

        _, im = self.load_colour(shape, col)

        photo = ImageTk.PhotoImage(im)

        tag = board.create_image(x + dx / 2, y + dy / 2, image=photo)

        self.copies[(i, j)] = photo
        board.piece_tags[(i, j)] = tag

    def draw_text(self, game, pos, shape, col):
        self.undraw(game, pos)

        board = game.board
        i, j = pos
        w, h = board.winfo_width(), board.winfo_height()
        dx, dy = w / board.nx, h / board.ny
        x, y = i * dx + dx/2, j * dy + dy/2

        if col:
            tag = board.create_text(x, y, text=shape, fill=col)
        else:
            tag = board.create_text(x, y, text=shape)

        board.piece_tags[(i, j)] = tag

    def undraw(self, game, pos):
        board = game.board

        pos = tuple(pos)

        tag = board.piece_tags.get(pos, None)

        if tag is not None:
            board.delete(tag)
            del board.piece_tags[pos]

        if pos in self.copies:
            del self.copies[pos]

    def process(self, game: Chess, effect, args):
        if effect == "draw_piece":
            piece = game.board.get_tile(args).piece

            if piece:
                shape = piece.shape
                col = piece.get_colour()
            else:
                shape = col = ""

            return [("draw_piece_at_cmap", (args, shape, col))]
        elif effect == "draw_piece_at":
            pos, shape, col = args

            # don't put None in files unless you want something fun to happen
            if shape in self.files:  # draw image
                self.draw_image(game, pos, shape, col)
            elif shape:  # draw text
                self.draw_text(game, pos, shape, col)
            else:  # undraw
                self.undraw(game, pos)


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
                tag = board.piece_tags[pos]

                if board.type(tag) == "image":
                    return [("draw_piece_at_cmap", (pos, piece.shape, col))]
                elif board.type(tag) == "text":
                    board.itemconfig(tag, fill=col)


__all__ = ['DrawInitRule', 'RedrawRule', 'SelectRule', 'fill_opaque', 'DrawPieceRule', 'MarkCMAPRule', 'hex_to_rgb',
           'MarkRule', 'DrawSetPieceRule', 'DrawPieceCMAPRule', 'IndicatorRule', 'MarkValidRule', 'search']
