import asyncio
import json
import time

import numpy as np

from typing import List

import websockets

from structures.colours import *
from structures.chess_structures import *
from structures.structures import *
from rules.rules import *


class RedrawRule2(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["redraw"])

    def process(self, game: Chess, effect, args):
        if effect == "redraw":
            board = game.board

            draw_list = []
            for ix, v in np.ndenumerate(board.tiles):
                draw_list += [("draw_piece", ix)]

            return draw_list


class MarkRule2(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["mark"])

    def process(self, game: Chess, effect, args):
        if effect == "mark":
            pos, col = args

            board = game.board
            piece = board.get_tile(pos).get_piece()

            if piece:
                return [("draw_piece_at_cmap", (pos, piece.shape, col))]


class MarkValidRule2(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        Rule.__init__(self, watch=["selected", "unselected"])
        self.subruleset = subruleset
        self.move0 = move0

        self.tags = []

        self.success_indicator = IndicatorRule(["move_success"])
        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        elist = []
        if effect == "selected":
            valid = list(search_valid(self, game, around=args))

            for pos in valid:
                self.tags += [pos]
                elist += [("overlay", (pos, "x", HEXCOL["valid"]))]
        elif effect == "unselected":
            for tag in self.tags:
                elist += [("overlay", (tag, "", HEXCOL["valid"]))]
            self.tags = []

        return elist


class StatusRule(Rule):
    def __init__(self):
        Rule.__init__(self, watch=["turn_changed", "connect", "wins", "turn_unlocked"])

        self.won = False

    def process(self, game: Chess, effect: str, args):
        if self.won:
            return

        if effect in ["turn_changed", "connect", "turn_unlocked"]:
            return [("status", game.get_turn() + " turn")]
        if effect == "wins":
            self.won = True
            return [("status", args + " won")]


class PromoteStartRule(Rule):
    def __init__(self, eligible: List[str], promotions: List[str]):
        Rule.__init__(self, watch=["moved"])

        self.eligible = eligible
        self.promotions = promotions

    def process(self, game: Chess, effect: str, args):
        if effect == "moved":
            piece_id, start, end = args

            piece = game.get_by_id(piece_id)
            shape = piece.shape
            col = piece.get_colour()

            if col not in game.get_player():
                return

            board = game.get_board()
            y = 0 if col == "w" else board.ny - 1

            if end[1] == y:
                if shape in self.eligible:
                    return [("lock_turn", ()), ("promoting", (end, col)),
                            ("askstring", ("Promote to: " + str(self.promotions), col))]


class LockRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["lock_turn", "unlock_turn"])

        self.turn = None

    def process(self, game: Chess, effect: str, args):
        if effect == "lock_turn":
            if not self.turn:
                self.turn = game.get_turn()
                game.turn = ""

        if effect == "unlock_turn":
            if self.turn:
                game.turn = self.turn
                self.turn = None
                return [("turn_unlocked", ())]


class WinStopRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["wins"])

    def process(self, game: Game, effect: str, args):
        return [("lock_turn", ()), ("stop", ())]


class PromoteReadRule(Rule):
    def __init__(self, promotions: List[str]):
        Rule.__init__(self, watch=["promoting", "readstring"])

        self.promotions = promotions
        self.promoting = None

    def process(self, game: Chess, effect: str, args):
        if effect == "promoting":
            self.promoting = args
        elif effect == "readstring":
            if self.promoting:
                text, player = args
                end, col = self.promoting

                if not player == col:
                    return [("askstring", ("Promote to: " + str(self.promotions), col))]

                if text in self.promotions:
                    self.promoting = None
                    return [("take", end), ("unlock_turn", ()), ("create_piece", (end, col, text))]
                else:
                    return [("askstring", ("Promote to: " + str(self.promotions), col))]


class SendFilterRule(Rule):
    def __init__(self, filter_all: List[str]):
        Rule.__init__(self, ["send", "set_filter"])

        self.filter_all = filter_all
        self.filter = filter_all

    def process(self, game: Game, effect: str, args):
        if effect == "send":
            return [("send_filter", (args, self.filter))]
        elif effect == "set_filter":
            if args == "all":
                self.filter = self.filter_all
            else:
                self.filter = args


class WebSocketRule(Rule):
    def __init__(self, game: Chess, player: str, ws: websockets.WebSocketServerProtocol):
        Rule.__init__(self, ["send_raw", "send_filter"])

        self.game = game
        self.ws = ws
        self.player = player

    def process(self, game: Game, effect: str, args):

        if effect == "send_raw":
            out = json.dumps(args)
        elif effect == "send_filter" and self.player in args[1]:
            out = json.dumps(args[0])
        else:
            return

        asyncio.run_coroutine_threadsafe(self.ws.send(out), asyncio.get_event_loop())

    async def run(self):
        self.game.process("connect", self.player)
        try:
            async for msg in self.ws:
                data = json.loads(msg)

                eff, arg = data
                if eff == "click":
                    self.game.process("touch", (arg, self.player))
                elif eff == "write":
                    self.game.process("readstring", (arg, self.player))
        finally:
            self.game.ruleset.remove_rule(self)
            self.game.process("disconnect", self.player)


class ConnectRedrawRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["connect"])

    def process(self, game: Game, effect: str, args):
        if effect == "connect":
            return [("redraw", ())]


class DrawReplaceRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["draw_piece_at"])

        self.table = {"K": "\u2654", "D": "\u2655", "T": "\u2656", "L": "\u2657", "P": "\u2658", "p": "\u2659",
                      "S": "\U0001fa11"}

    def process(self, game: Game, effect: str, args):
        if effect == "draw_piece_at":
            pos, shape, col = args
            shape = self.table.get(shape, shape)

            return [("draw_piece_at2", (pos, shape, col))]


class WebTranslateRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["draw_piece_at", "draw_piece", "overlay", "status", "askstring"])

    def process(self, game: Chess, effect: str, args):
        if effect == "draw_piece_at2":
            return [("send", ("draw_piece", args))]
        elif effect == "draw_piece":
            piece = game.get_board().get_tile(args).piece

            if piece:
                shape = piece.shape
                col = piece.get_colour()
            else:
                shape = col = ""

            return [("draw_piece_at_cmap", (args, shape, col))]
        elif effect in ["overlay", "status"]:
            return [("send", (effect, args))]
        elif effect == "askstring":
            return [("send_filter", ((effect, args[0]), args[1]))]


class CloseRoomRule(Rule):
    def __init__(self, server, room: str):
        Rule.__init__(self, ["stop"])

        self.server = server
        self.room = room

    def process(self, game: Chess, effect: str, args):
        self.server.close_room(self.room)


class TimeoutRule(Rule):
    def __init__(self, ruleset: Ruleset, timeout: int, watch: List[str]):
        Rule.__init__(self, watch=watch + ["init"])

        self.ruleset = ruleset
        self.timeout = timeout
        self.last_event = time.perf_counter()

    async def poll_timeout(self):
        while True:
            if time.perf_counter() - self.last_event > self.timeout:
                self.ruleset.process("stop", ())
                return

            await asyncio.sleep(self.timeout)

    def process(self, game: Chess, effect: str, args):
        if effect == "init":
            asyncio.run_coroutine_threadsafe(self.poll_timeout(), asyncio.get_event_loop())

        self.timeout = time.perf_counter()


__all__ = ["RedrawRule2", "MarkRule2", "MarkValidRule2", "StatusRule", "PromoteReadRule", "LockRule", "WinStopRule",
           "PromoteStartRule", "WebSocketRule", "ConnectRedrawRule", "WebTranslateRule", "CloseRoomRule", "TimeoutRule",
           "SendFilterRule", "DrawReplaceRule"]
