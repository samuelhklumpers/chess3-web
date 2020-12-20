import json
import random
import socket
import threading
import time
import tkinter as tk
import traceback
from tkinter import simpledialog

import numpy as np
import itertools as itr

from chess_rules import *
from chess_structures import *
from drawing import *


class OnlineDialog(simpledialog.Dialog):
    def __init__(self, parent):
        simpledialog.Dialog.__init__(self, title="Online Chess", parent=parent)

    def body(self, master):
        self.raddr = tk.StringVar()
        self.lport = tk.StringVar()
        self.rport = tk.StringVar()
        self.active = tk.BooleanVar()

        addr_label = tk.Label(master, text="Address:", justify=tk.LEFT)
        addr_entry = tk.Entry(master, textvariable=self.raddr)

        local_label = tk.Label(master, text="Local port (empty defaults to remote port):", justify=tk.LEFT)
        local_entry = tk.Entry(master, textvariable=self.lport)

        remote_label = tk.Label(master, text="Remote port:", justify=tk.LEFT)
        remote_entry = tk.Entry(master, textvariable=self.rport)

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
        addr, lport, rport, active = self.raddr.get(), self.lport.get(), self.rport.get(), self.active.get()

        if rport:
            if lport:
                ...
            else:
                lport = rport

            lport = int(lport)
            rport = int(rport)
        else:
            return False

        self.result = addr, lport, rport, active
        return True


def make_socket(remote_address, remote_port, local_port=None, active=True):
    if not local_port:
        local_port = remote_port

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", local_port))

    def listen(s, ret):
        print("listening")
        s.listen(0)
        s, a = s.accept()
        print("accepted", a)

        ret.append((s, a))

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
        ret = []

        t = threading.Thread(target=lambda: listen(s, ret))
        t.start()

        try:
            while t.is_alive():
                t.join(1)
            s, a = ret[0]
        except:
            s.close()
            t.join()
            print("stopping listening")
            return

    print("connected")

    return s


def chain_rules(steps, base):
    rules = []
    out_effect = intro = base + "0"
    for i, step in enumerate(steps, start=1):
        in_effect = out_effect
        out_effect = base + str(i)

        for rule in step:
            inst = rule(in_effect, out_effect)
            rules.append(inst)

    return intro, rules, out_effect


def play_chess(online=True):
    chess = Chess()

    if online:
        dialog = OnlineDialog(chess)
        addr, lport, rport, active = dialog.result

        sock = make_socket(addr, lport, rport, active)

        chess.set_socket(sock)
    ruleset = Ruleset(chess)

    move_rules = [
        [IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule],
        [PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule, BishopRule, RookRule,
         QueenRule, KingRule, CastleRule]
    ]

    move0, move_rules, move1 = chain_rules(move_rules, "move")
    drawing = [DrawInitRule(), RedrawRule(), MarkRule(), SelectRule(), MarkCMAPRule(), DrawPieceRule()]
    actions = [TouchMoveRule(move0), TakeRule(), MoveTakeRule(move1), SetPieceRule(), SetPlayerRule(), MoveRedrawRule(), NextTurnRule()]
    post_move = [MovedRule(), PawnPostDouble()]
    win_cond = [WinRule(), WinCloseRule()]
    network = [ReceiveRule(), SendRule([move1, "exit"]), CloseSocket()]

    ruleset.add_all(move_rules)
    ruleset.add_all(drawing)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)
    ruleset.add_all(win_cond)
    if online:
        ruleset.add_all(network)
    ruleset.add_rule(ExitRule(), -1)
    ruleset.add_rule(CreatePieceRule())
    ruleset.add_rule(CounterRule())

    chess.set_ruleset(ruleset)

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")
    ruleset.process("init", ())


    chess.geometry("600x600")

    chess.mainloop()


from fairy_rules import *


def play_fairy_variant():
    chess = Chess()

    dialog = OnlineDialog(chess)
    addr, lport, rport, active = dialog.result

    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)
    chess.load_board_str("wa8Sh8Sb8Rg8Rc8Cf8Cd8]e8Ma7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;ba1Sh1Sb1Rg1Rc1Cf1Cd1]e1Ma2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F")

    ruleset = Ruleset(chess)

    move_rules = [
        [IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule],
        [FighterRule, RiderRule, KirinRule, SniperRule,
         SquareRule, MasterRule]
    ]

    move0, move_rules, move1 = chain_rules(move_rules, "move")
    actions = [TouchMoveRule(move0), TakeRule(), MoveTakeRule(move1), SetPieceRule(), MoveRedrawRule(), NextTurnRule()]
    post_move = [MovedRule(), PawnPostDouble()]
    win_cond = [FairyWinRule(), WinCloseRule()]
    network = [ReceiveRule(), SendRule([move0, "exit"]), CloseSocket()]

    ruleset.add_all(move_rules)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)
    ruleset.add_all(win_cond)
    ruleset.add_all(network)
    ruleset.add_rule(ExitRule(), -1)

    chess.set_ruleset(ruleset)
    ruleset.process("init", ())

    chess.board.redraw()

    chess.mainloop()


if __name__ == '__main__':
    play_chess(online=True)