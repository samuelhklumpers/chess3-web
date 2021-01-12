import asyncio
import json
import logging
import os
import sys
import threading
import time
import websockets

from functools import partial

from server.server_rules import *
from rules.chess_rules import *
from rules.normal_chess_rules import *
from rules.fairy_rules import *
from structures.chess_structures import *
from rules.drawing_rules import *
from structures.structures import *
from rules.rules import *


logging.basicConfig(filename="gameserver.log", level=logging.WARNING)


def server_actions(move_start):
    return [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(), SetPieceRule(), SetPlayerRule(),
            WebTranslateRule(), ConnectRedrawRule(), StatusRule(), LockRule(), WinStopRule()]


def make_markvalid(game, piece_move, move_start):
    # setup valid move marking
    pure_types = [[IdMoveRule], [FriendlyFireRule]] + piece_move  # pure moves (i.e. no side effects)
    pure0, pure, pure1 = chain_rules(pure_types, "move")

    subruleset = Ruleset(game)  # create new logic system
    subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

    subruleset.add_all(pure)
    subruleset.add_rule(SuccesfulMoveRule(pure1))

    return MarkValidRule2(subruleset, move_start)


def setup_chess(mode):
    game = Chess()

    board = Board(game)
    board.make_tiles(NormalTile)
    game.set_board(board)

    ruleset = game.ruleset

    base_move = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
    normal_drawing = [DrawSetPieceRule(), DrawPieceCMAPRule(), RedrawRule2(), SelectRule(), SelectRule(),
                      MarkCMAPRule(), MarkRule2()]

    late = [NextTurnRule()]

    ruleset.add_rule(TimeoutRule(ruleset, 10 * 60, watch=["touch", "readstring"]))

    if mode == "normal":
        special = [CreatePieceRule({"K": MovedPiece, "p": Pawn, "T": MovedPiece})]

        piece_move = [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                      BishopRule, RookRule, QueenRule, KingRule, CastleRule]]

        move_constrs = base_move + piece_move
        move_start, moves, move_end = chain_rules(move_constrs, "move")
        moves += [SuccesfulMoveRule(move_end)]

        post_move = [MovedRule(), PawnPostDouble(), PromoteStartRule(["p"], ["L", "P", "T", "D"]),
                     PromoteReadRule(["L", "P", "T", "D"]), WinRule()]

        actions = server_actions(move_start)

        drawing = normal_drawing + [make_markvalid(game, piece_move, move_start)]

        ruleset.add_all(special + moves + post_move + actions + drawing)
        ruleset.add_all(late, prio=-2)

        start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
                "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"
    elif mode == "fairy":
        special = [CreatePieceRule({})]

        piece_move = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

        move_constrs = base_move + piece_move
        move_start, moves, move_end = chain_rules(move_constrs, "move")
        moves += [SuccesfulMoveRule(move_end)]

        post_move = [MovedRule(), PromoteStartRule(["F"], ["J", "C", "S", "W"]), PromoteReadRule(["J", "C", "S", "W"]),
                     WinRule()]

        actions = server_actions(move_start)

        drawing = normal_drawing + [make_markvalid(game, piece_move, move_start)]

        ruleset.add_all(special + moves + post_move + actions + drawing)

        start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;" \
                "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"
    else:
        return

    game.load_board_str(start)
    ruleset.process("init", ())

    return game


class GameServer:
    def __init__(self, port):
        self.port = port
        self.games = {}

    def run(self):
        start_server = websockets.serve(self.accept, "", self.port)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def do_room(self, ws, mode, room_id, user_id):
        if room_id not in self.games:
            chess = setup_chess(mode)
            chess.ruleset.add_rule(CloseRoomRule(self, room_id))
            self.games[room_id] = {"game": chess, "players": {}, "sockets": []}
        room_data = self.games[room_id]

        chess = room_data["game"]
        sockets = room_data["sockets"]

        sockets.append(ws)

        players = room_data["players"]
        if user_id in players:
            colour = players[user_id]
        else:
            if len(players) == 0:
                colour = "w"
            elif len(players) == 1:
                colour = "b"
            else:
                colour = "none"
        players[user_id] = colour

        ws_rule = WebSocketRule(chess, colour, ws)
        chess.ruleset.add_rule(ws_rule)

        await ws_rule.run()

    def close_room(self, room):
        try:
            room_data = self.games[room]

            for ws in room_data["sockets"]:
                ws.close()
        finally:
            del self.games[room]

    async def accept(self, ws: websockets.WebSocketServerProtocol, path):
        print(path)
        if path != "/":
            await ws.close()
            return

        try:
            msg = await ws.recv()

            data = json.loads(msg)
            mode, room_id, user_id = data["mode"], data["room"], data["user"]
            room_id = room_id + "_" + mode

            await self.do_room(ws, mode, room_id, user_id)
        finally:
            await ws.close()


def thread_loop(port):
    responsive = threading.Event()
    responsive.set()
    error_times = []

    error_timeout = 10 * 60
    restart_timeout = 60
    max_errors = 4

    while True:
        for t in error_times.copy():
            now = time.perf_counter()
            if now - t > error_timeout:
                error_times.remove(t)

        if len(error_times) > max_errors:
            logging.log(logging.WARNING, f"encountered {max_errors+1} errors in {error_timeout}s, exiting")
            return

        th = threading.Thread(target=partial(open_server, port=port, responsive=responsive, errors=error_times))
        th.start()
        while th.is_alive() and responsive.is_set():
            responsive.clear()
            th.join(10)

        if th.is_alive() and not responsive.is_set():
            logging.log(logging.ERROR, "server thread became unresponsive, crashing")
            os._exit(1)

        time.sleep(restart_timeout)


def open_server(port, responsive, errors):
    asyncio.set_event_loop(asyncio.new_event_loop())

    async def set_responsive_task():
        while True:
            responsive.set()
            await asyncio.sleep(5)

    try:
        asyncio.run_coroutine_threadsafe(set_responsive_task(), asyncio.get_event_loop())
        gameserver = GameServer(port=port)
        gameserver.run()
    except Exception:
        logging.error("game server encountered unexpected state", exc_info=sys.exc_info())
        errors.append(time.perf_counter())
