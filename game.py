import threading
import tkinter as tk

import numpy as np
import itertools as itr


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itr.zip_longest(*args, fillvalue=fillvalue)


def srange(f, t, s=1):
    s = abs(s)

    sgn = np.sign(t - f)
    sgn = sgn if sgn else 1

    return range(f, t, sgn * s)


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

    def add_rule(self, rule, prio=1):
        # 0 forbidden/debug
        # -1 forbidden/debug
        self.rules.setdefault(prio, []).append(rule)

    def process_all(self, elist):
        print(elist)
        for effect, args in elist:
            self.process(effect, args)

    def process(self, effect, args):
        with self.lock:
            self._process(effect, args)

    def _process(self, effect, args):
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


class PawnRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "p":
                return [("move4", args)]


class KnightRule(Rule):
    def process(self, game, effect, args):
        if effect == "move3":
            piece = game.board.get_tile(args[0]).get_piece()
            if piece.shape == "P":
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

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
                x1, y1 = args[0]
                x2, y2 = args[1]

                dx, dy = x2 - x1, y2 - y1

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return [("move4", args)]


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
        self.moved = 0
        self.double = False

    def get_colour(self):
        return self.col


class Chess(Game):
    def __init__(self):
        Game.__init__(self)

        self.ruleset = None
        self.object_map = {0: None}
        self.obj_count = 1
        self.board = SquareBoardWidget(self)
        self.turn = "w"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board.grid(sticky="nsew")

    def set_ruleset(self, ruleset):
        self.ruleset = ruleset

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
                self.add_object(piece)


def play_chess():
    chess = Chess()

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")

    ruleset = Ruleset(chess)
    ruleset.add_rule(TouchMoveRule())
    ruleset.add_rule(IdMoveRule())
    ruleset.add_rule(MoveTurnRule())
    ruleset.add_rule(MoveTakeRule())
    ruleset.add_rule(FriendlyFireRule())
    ruleset.add_rule(SetPieceRule())
    ruleset.add_rule(RedrawRule())
    ruleset.add_rule(NextTurnRule())

    ruleset.add_rule(PawnRule())
    ruleset.add_rule(KnightRule())
    ruleset.add_rule(BishopRule())
    ruleset.add_rule(RookRule())
    ruleset.add_rule(QueenRule())
    ruleset.add_rule(KingRule())

    ruleset.add_rule(WinRule())

    chess.set_ruleset(ruleset)

    chess.mainloop()


if __name__ == '__main__':
    play_chess()