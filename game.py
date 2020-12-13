import json
import random
import select
import socket
import threading
import time
import tkinter as tk
import traceback
from abc import ABC, abstractmethod
from tkinter import simpledialog

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

        self.protocol("WM_DELETE_WINDOW", self.cleanup)

    def cleanup(self, event=None):
        self.destroy()


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
    def __init__(self, effects):
        self.effects = effects
        self.touched = None
        self.turn_num = 0
        self.won = None

    def pass_turn(self):
        self.effects.force_state("turn_num", self.turn_num + 1)

    def check_won(self, board):
        kings = {}

        for tile in board.tiles.flat:
            piece = tile.piece

            if piece and piece.shape == "K":
                kings.setdefault(piece.col, 0)
                kings[piece.col] += 1

        not_dead = [c for c in kings if kings[c] > 0]
        alive = len(not_dead)

        if alive > 1:
            ...
        elif alive == 1:
            self.effects.force_state("won", not_dead[0])
        else:
            self.effects.force_state("won", "nobody")

    def process(self, board: SquareBoardWidget, pos):
        if self.won:
            return

        move = self.touch(board, pos)

        if move:
            self.move(*move)

        self.check_won(board)

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

    def move(self, board, pos1, pos2, turn=True):
        if pos1 == pos2:
            return

        self.effects.force_move(pos1, pos2)

        if turn:
            self.pass_turn()

        board.redraw()


class TurnChess(FreeChess):
    def __init__(self, effects):
        FreeChess.__init__(self, effects)

        self.turn = "w"
        self.allowed = "wb"

    def pass_turn(self):
        FreeChess.pass_turn(self)

        self.effects.force_state("turn", "b" if self.turn == "w" else "w")

    def set_player(self, p):
        self.allowed = p

    def touch(self, board: SquareBoardWidget, tile_i):
        if not self.turn in self.allowed:
            return ()

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
    def __init__(self, effects):
        FreeChess.__init__(self, effects)

    def move(self, board, pos1, pos2, turn=True):
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

            if self.castle(board, pos1, pos2, piece1, dp):
                return
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
            pawn_dp = np.array(pawn_dp)

            start = 6 if c == "w" else 1
            first = start == pos1[1]

            can = (not piece2 and (np.all(dp == pawn_dp) or (first and np.all(dp == 2 * pawn_dp)))) or (piece2 and dp[1] == pawn_dp[1] and abs(dp[0]) == 1)

            if can and abs(dp[1]) == 2:
                piece1.double = True

            if self.en_passant(board, pos1, pos2, piece1, dp, pawn_dp):
                return

        if can:
            FreeChess.move(self, board, pos1, pos2, turn=turn)

    def castle(self, board, pos1, pos2, piece1, dp):
        if piece1.moved:
            return False

        if abs(dp[0]) != 2 or dp[1] != 0:
            return False

        pos3 = pos1 + dp // 2
        pos4 = np.array(pos2) + [np.sign(dp[0]) - (1 if dp[0] < 0 else 0), 0]

        pos3 = tuple(pos3)
        pos4 = tuple(pos4)

        piece2 = board.tiles[pos4].piece

        if not piece2 or piece2.shape != "T" or piece2.moved:
            return False

        FreeChess.move(self, board, pos1, pos2, turn=False)
        FreeChess.move(self, board, pos4, pos3)

    def en_passant(self, board, pos1, pos2, piece1, dp, pawn_dp):
        pos1 = np.array(pos1)

        if np.all(dp == pawn_dp + [1, 0]):
            pos3 = pos1 + [1, 0]
        elif np.all(dp == pawn_dp - [1, 0]):
            pos3 = pos1 - [1, 0]
        else:
            return False

        pos1 = tuple(pos1)
        pos3 = tuple(pos3)

        piece2 = board.tiles[pos3].piece

        if not piece2 or piece2.moved != self.turn_num or not piece2.double or piece1.col == piece2.col:
            return False

        board.tiles[pos3].piece = None
        FreeChess.move(self, board, pos1, pos2)


class MoveTurnChess(MoveChess, TurnChess):
    def __init__(self, effects):
        MoveChess.__init__(self, effects)
        TurnChess.__init__(self, effects)

    def process(self, board: SquareBoardWidget, pos):
        if self.won:
            return

        move = TurnChess.touch(self, board, pos)
        if move:
            MoveChess.move(self, *move)
            self.check_won(board)


class NormalTile:
    def __init__(self):
        self.piece = None


class Piece:
    def __init__(self, shape="A", col="w"):
        self.shape = shape
        self.col = col
        self.moved = 0
        self.double = False


class Worker(ABC):
    def __init__(self):
        self.thread = None

    def start(self):
        if not self.is_running():
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    @abstractmethod
    def run(self):
        ...

    def is_running(self):
        return self.thread and self.thread.is_alive()

    @abstractmethod
    def halt(self):
        ...

    def stop(self):
        if self.thread is None:
            return

        if self.is_running():
            self.halt()

        try:
            self.thread.join(timeout=1)
        except:
            ...

        if self.is_running():
            raise RuntimeError("Thread is still alive")

        self.thread = None


class Effects(Worker):
    def __init__(self, game, board, sock=None, online=False):
        Worker.__init__(self)

        self.game = game
        self.board = board
        self.sock = sock
        self.online = online
        self.running = False
        self.cond = None

    def process(self, cmd):
        for part in cmd.split(b";"):
            if not part:
                continue

            tgt, args = json.loads(part.decode())

            if tgt == "tile":
                self.force_tile(tuple(args[0]), *args[1:], recv=True)
            elif tgt == "state":
                self.force_state(*args, recv=True)
            elif tgt == "move":
                self.force_move(tuple(args[0]), tuple(args[1]), recv=True)

            self.board.after_idle(self.board.redraw)

    def send(self, cmd):
        js = json.dumps(cmd)
        js += ";"

        self.sock.send(js.encode())

    def force_tile(self, tile_ix, attr, val, recv=False):
        self.board.tiles[tile_ix].__setattr__(attr, val)

        if self.online and not recv:
            cmd = ("tile", (tile_ix, attr, val))
            self.send(cmd)

    def force_move(self, pos1, pos2, recv=False):
        board = self.board

        tile1 = board.tiles[pos1]
        tile2 = board.tiles[pos2]

        tile2.piece = tile1.piece
        tile1.piece = None

        tile2.piece.moved = self.board.rules.turn_num + 1

        if self.online and not recv:
            cmd = ("move", (pos1, pos2))
            self.send(cmd)

    def force_state(self, attr, val, recv=False):
        self.board.rules.__setattr__(attr, val)

        if attr == "won":  # xd
            print(val, "won")

        if self.online and not recv:
            cmd = ("state", (attr, val))
            self.send(cmd)

    def decide_colour(self):
        roll = random.getrandbits(64)

        self.sock.send(str(roll).encode())

        other = int(self.sock.recv(1024).decode())

        if roll > other:
            print("You are playing as white")
            self.board.rules.set_player("w")
        else:
            print("You are playing as black")
            self.board.rules.set_player("b")

    def run(self):
        try:
            self.running = True
            self.cond = threading.Condition()
            self.sock.settimeout(1)

            self.decide_colour()

            with self.cond:
                while self.running:
                    try:
                        data = self.sock.recv(1024)

                        if data:
                            self.process(data)
                        else:
                            self.halt()
                    except socket.timeout:
                        self.cond.wait(1)
        except Exception:
            traceback.print_exc()
            self.halt()

    def halt(self):
        if self.running:
            self.running = False

        if self.cond:
            res = self.cond.acquire(blocking=False)

            if res:
                self.cond.notify()
                self.cond.release()
            else:
                print(self, "blocked!")

        try:
            self.sock.shutdown(0)
            self.sock.close()
        except OSError:
            ...


class Chess(Game):
    def __init__(self, sock=None):
        Game.__init__(self)

        self.board = SquareBoardWidget(self)

        self.effects = Effects(self, self.board, sock=sock, online=bool(sock))

        self.board.set_rules(MoveTurnChess(self.effects))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board.grid(sticky="nsew")

        if sock:
            self.after_idle(lambda event=None: self.effects.start())

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

    def cleanup(self, event=None):
        if self.effects.online:
            self.effects.halt()

        Game.cleanup(self)


def make_socket(remote_address, remote_port, local_port=None, active=True):
    if not local_port:
        local_port = remote_port

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(("", local_port))

    if active:
        print("trying to connect", (remote_address, remote_port))

        while True:
            try:
                s.connect((remote_address, remote_port))
                break
            except:
                traceback.print_exc()
                print("retrying")
                time.sleep(10)
    else:
        print("listening")
        s.listen(0)

        s, a = s.accept()
        print("accepted", a)

    print("connected")

    return s


class OnlineDialog(simpledialog.Dialog):
    def __init__(self):
        self.root = tk.Tk()

        simpledialog.Dialog.__init__(self, title="Online Chess", parent=self.root)

        self.address = None
        self.this_port = None
        self.other_port = None
        self.active = None

    def body(self, master):
        self.address = tk.StringVar()
        self.this_port = tk.StringVar()
        self.other_port = tk.StringVar()
        self.active = tk.BooleanVar()

        addr_label = tk.Label(master, text="Address:", justify=tk.LEFT)
        addr_entry = tk.Entry(master, textvariable=self.address)

        local_label = tk.Label(master, text="Local port (empty defaults to remote port):", justify=tk.LEFT)
        local_entry = tk.Entry(master, textvariable=self.this_port)

        remote_label = tk.Label(master, text="Remote port:", justify=tk.LEFT)
        remote_entry = tk.Entry(master, textvariable=self.other_port)

        active_label = tk.Label(master, text="Active:", justify=tk.LEFT)
        active_tickbox = tk.Checkbutton(master, variable=self.active)

        addr_label.grid(row=0, column=0)
        addr_entry.grid(row=0, column=1)

        local_label.grid(row=1, column=0)
        local_entry.grid(row=1, column=1)

        remote_label.grid(row=2, column=0)
        remote_entry.grid(row=2, column=1)

        active_label.grid(row=3, column=0)
        active_tickbox.grid(row=3, column=1)

        return addr_entry

    def validate(self):
        addr, lport, rport, active = self.address.get(), self.this_port.get(), self.other_port.get(), self.active.get()
        lport = int(lport) if lport else rport
        rport = int(rport) if rport else rport

        self.result = addr, lport, rport, active
        print(self.result)
        return True

    def get_result(self):
        self.root.destroy()
        return self.result


def play_chess(online=False):
    if online:
        dialog = OnlineDialog()

        addr, local_port, remote_port, active = dialog.get_result()

        sock = make_socket(addr, remote_port, local_port, active)
    else:
        sock = None

    chess = Chess(sock=sock)

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")

    chess.mainloop()


if __name__ == '__main__':
    play_chess(online=True)