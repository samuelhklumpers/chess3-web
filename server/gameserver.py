import asyncio
import json
import logging
import os
import sys
import threading
import time
import traceback

import websockets

from functools import partial

from server.server_rules import *
from rules.chess_rules import *
from rules.normal_chess_rules import *
from rules.fairy_rules import *
from rules.shogi_rules import *
from structures.shogi_structures import *
from structures.chess_structures import *
from rules.drawing_rules import *
from structures.structures import *
from rules.rules import *
from rules.line_of_sight_rules import *


logging.basicConfig(filename="gameserver.log", level=logging.WARNING)


def min_server_actions():
    return [TakeRule(), MoveTakeRule(), SetPieceRule(), SetPlayerRule(),
            WebTranslateRule(), StatusRule(), LockRule(), SendFilterRule(["b", "w"]), TouchStartsTurnRule("touch")]


def server_actions():
    return min_server_actions() + [ConnectRedrawRule()]


def make_pure_moves(game, piece_move):
    pure_types = [[IdMoveRule], [FriendlyFireRule]] + piece_move  # pure moves (i.e. no side effects)
    pure0, pure, pure1 = chain_rules(pure_types, "move")

    subruleset = Ruleset(game)  # create new logic system
    subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

    subruleset.add_all(pure)
    subruleset.add_rule(SuccesfulMoveRule(pure1))

    return subruleset


def make_markvalid(game, piece_move, move_start):
    subruleset = make_pure_moves(game, piece_move)
    return MarkValidRule2(subruleset, move_start)


def setup_chess(mode):
    game = Chess()

    ruleset = game.ruleset
    ruleset.add_rule(TimeoutRule(ruleset, 10 * 60, watch=["touch", "readstring"]))
    ruleset.add_rule(WinStopRule(), -1)

    base_move = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
    lazy_drawing = [DrawPieceCMAPRule(), RedrawRule2(), MarkCMAPRule(), MarkRule2()]
    normal_drawing = lazy_drawing + [DrawSetPieceRule(), SelectRule()]
    late = [NextTurnRule(), WinCloseRule()]

    if mode == "normal":
        board = Board(game)
        board.make_tiles(NormalTile)
        game.set_board(board)

        special = [CreatePieceRule({"K": MovedPiece, "p": Pawn, "T": MovedPiece})]

        piece_move = [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                      BishopRule, RookRule, QueenRule, KingRule, CastleRule]]

        move_start, moves, move_end = chain_rules(base_move + piece_move, "move")
        moves.append(SuccesfulMoveRule(move_end))

        post_move = [MovedRule(), PawnPostDouble(), PromoteStartRule(["p"], ["L", "P", "T", "D"]),
                     PromoteReadRule(["L", "P", "T", "D"]), WinRule()]

        actions = server_actions()
        actions.append(TouchMoveRule(move_start))

        ruleset.add_rule(ConnectSetupRule({"board_size": (8, 8)}), 0)

        draw_table = {"K": "king.svg", "D": "queen.svg", "T": "rook.svg", "L": "bishop.svg", "P": "knight.svg",
                      "p": "pawn.svg"}

        start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
                "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"
        drawing = normal_drawing
        drawing.append(make_markvalid(game, piece_move, move_start))
        # can't have this in LoS because then 2nd order moves tell positions of unseen :p
    elif mode == "fairy":
        board = Board(game)
        board.make_tiles(NormalTile)
        game.set_board(board)

        special = [CreatePieceRule({})]

        piece_move = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

        move_start, moves, move_end = chain_rules(base_move + piece_move, "move")
        moves.append(SuccesfulMoveRule(move_end))

        post_move = [MovedRule(), PromoteStartRule(["F"], ["J", "C", "S", "W"]), PromoteReadRule(["J", "C", "S", "W"]),
                     WinRule()]

        actions = server_actions()
        actions.append(TouchMoveRule(move_start))

        ruleset.add_rule(ConnectSetupRule({"board_size": (8, 8)}), 0)

        draw_table = {"K": "king.svg", "F": "ferz.svg", "S": "shooter.svg", "J": "jumper.svg", "C": "kirin.svg",
                      "W": "wheel.svg"}

        start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;" \
                "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"
        drawing = normal_drawing
        drawing.append(make_markvalid(game, piece_move, move_start))
    elif mode == "shogi":
        board = ShogiBoard(game)
        board.make_tiles(NormalTile)
        game.set_board(board)

        special = [CreatePieceRule({}), DropRule()]

        piece_move = [[KingRule, SRookRule, DragonRule, SBishopRule, HorseRule, GoldRule,
                       SilverRule, PromotedSilverRule, CassiaRule, PromotedCassiaRule, Lance,
                       PromotedLanceRule, SoldierRule, PromotedSoldierRule]]

        post_move = [ShogiPromoteStartRule(), ShogiPromoteReadRule(), ShogiTakeRule(),
                     CaptureRule(), WinRule()]

        move_start, moves, move_end = chain_rules(base_move + piece_move, "move")
        moves += [SuccesfulMoveRule(move_end)]

        actions = server_actions()
        actions.append(ShogiTouchRule(move_start))

        ruleset.add_rule(ConnectSetupRule({"board_size": (9, 9)}), 0)

        draw_table = {"K": "king.svg", "L": "lance.svg", "N": "knight.svg", "S": "silver.svg", "G": "gold.svg",
                      "B": "bishop.svg", "R": "rook.svg", "P": "pawn.svg", "D": "dragon.svg", "H": "horse.svg",
                      "+P": "pawnplus.svg", "+S": "silverplus.svg", "+N": "knightplus.svg", "+L": "lanceplus.svg"}

        start = "wa9Lb9Nc9Sd9Ge9Kf9Gg9Sh9Ni9L" + "b8Bh8R" + "a7Pb7Pc7Pd7Pe7Pf7Pg7Ph7Pi7P;" \
                "ba1Lb1Nc1Sd1Ge1Kf1Gg1Sh1Ni1L" + "b2Rh2B" + "a3Pb3Pc3Pd3Pe3Pf3Pg3Ph3Pi3P"
        drawing = normal_drawing
        drawing.append(make_markvalid(game, piece_move, move_start))
    elif mode == "line":
        board = Board(game)
        board.make_tiles(NormalTile)
        game.set_board(board)

        special = [CreatePieceRule({"K": MovedPiece, "p": Pawn, "T": MovedPiece})]

        piece_move = [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                      BishopRule, RookRule, QueenRule, KingRule, CastleRule]]

        move_start, moves, move_end = chain_rules(base_move + piece_move, "move")
        moves.append(SuccesfulMoveRule(move_end))

        post_move = [MovedRule(), PawnPostDouble(), PromoteStartRule(["p"], ["L", "P", "T", "D"]),
                     PromoteReadRule(["L", "P", "T", "D"]), WinRule()]

        actions = min_server_actions()
        actions.append(TouchCensorRule("touch2"))
        actions.append(TouchMoveRule(move_start, cause="touch2"))

        ruleset.add_rule(ConnectSetupRule({"board_size": (8, 8)}), 0)

        draw_table = {"K": "king.svg", "D": "queen.svg", "T": "rook.svg", "L": "bishop.svg", "P": "knight.svg",
                      "p": "pawn.svg"}

        start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
                "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"
        drawing = lazy_drawing + [TurnFilterRule({"select": "select2"}), SelectRule("select2")]
        drawing.append(ServerLoSRule(make_pure_moves(game, piece_move), move_start))
    else:
        return

    drawing.append(DrawReplaceRule(draw_table))

    ruleset.add_all(special + moves + post_move + actions + drawing)
    ruleset.add_all(late, prio=-2)

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
                asyncio.run_coroutine_threadsafe(ws.close(), asyncio.get_event_loop())
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
        traceback.print_exc()
        logging.error("game server encountered unexpected state", exc_info=sys.exc_info())
        errors.append(time.perf_counter())
