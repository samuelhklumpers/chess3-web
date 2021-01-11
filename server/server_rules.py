import asyncio
import json

import numpy as np

from typing import List

from structures.colours import HEXCOL
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
            board = game.get_board()

            piece_id, start, end = args
            piece = game.get_by_id(piece_id)
            shape = piece.shape
            col = piece.get_colour()

            if col not in game.get_player():
                return

            y = 0 if col == "w" else board.ny - 1

            if end[1] == y:
                if shape in self.eligible:
                    return [("lock_turn", ()), ("promoting", (end, col)), ("askstring", ("Promote to: " + str(self.promotions), col))]


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

        if effect == "readstring":
            if self.promoting:
                text, player = args
                end, col = self.promoting

                if not player == col:
                    return [("askstring", ("Promote to: " + str(self.promotions), col))]

                elist = []
                elist += [("take", end), ("unlock_turn", ())]
                if text in self.promotions:
                    elist += [("create_piece", (end, col, text))]
                else:
                    return [("askstring", ("Promote to: " + str(self.promotions), col))]

                self.promoting = None

                return elist


class WebSocketRule(Rule):
    def __init__(self, game, player, ws):
        Rule.__init__(self, ["send", "send_filter"])

        self.game = game
        self.player = player
        self.ws = ws

    def process(self, game: Game, effect: str, args):

        if effect == "send":
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


class WebTranslateRule(Rule):
    def __init__(self):
        Rule.__init__(self, ["draw_piece_at", "draw_piece", "overlay", "status", "askstring"])

    def process(self, game: Chess, effect: str, args):
        if effect == "draw_piece_at":
            return [("send", ("draw_piece", args))]
        elif effect == "draw_piece":
            piece = game.board.get_tile(args).piece

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


class StopRule(Rule):
    def __init__(self, server, room):
        Rule.__init__(self, ["stop"])

        self.server = server
        self.room = room

    def process(self, game: Chess, effect: str, args):
        self.server.close_room(self.room)


class TimeoutRule(Rule):
    def __init__(self):
        ...  # raise stop if nothing happens for 10 minutes



__all__ = ["RedrawRule2", "MarkRule2", "MarkValidRule2", "StatusRule", "PromoteReadRule", "LockRule", "WinStopRule",
           "PromoteStartRule", "WebSocketRule", "ConnectRedrawRule", "WebTranslateRule", "StopRule"]