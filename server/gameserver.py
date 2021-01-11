import asyncio
import json
import websockets

from server.daemon import Daemon
from server.server_rules import *
from rules.chess_rules import *
from rules.normal_chess_rules import *
from rules.fairy_rules import *
from structures.chess_structures import *
from rules.drawing_rules import *
from structures.structures import *
from rules.rules import *


def setup_chess(mode):
    game = Chess()

    board = Board(game)
    board.make_tiles(NormalTile)
    game.set_board(board)

    ruleset = game.ruleset

    if mode == "normal":
        special = [CreatePieceRule({"K": MovedPiece, "p": Pawn, "T": MovedPiece})]

        base_move = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
        piece_move = [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                      BishopRule, RookRule, QueenRule, KingRule, CastleRule]]

        move_constrs = base_move + piece_move
        move_start, moves, move_end = chain_rules(move_constrs, "move")
        moves += [SuccesfulMoveRule(move_end)]

        post_move = [MovedRule(), PawnPostDouble(),
                     PromoteStartRule(["p"], ["L", "P", "T", "D"]),
                     PromoteReadRule(["L", "P", "T", "D"]),
                     WinRule()]

        actions = [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(), SetPieceRule(),
                   SetPlayerRule(), NextTurnRule(), WebTranslateRule(), ConnectRedrawRule(),
                   StatusRule(), LockRule(), WinStopRule()]

        # setup valid move marking
        pure_types = [[IdMoveRule], [FriendlyFireRule]] + piece_move  # pure moves (i.e. no side effects)
        pure0, pure, pure1 = chain_rules(pure_types, "move")

        subruleset = Ruleset(game)  # create new logic system
        subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

        subruleset.add_all(pure)
        subruleset.add_rule(SuccesfulMoveRule(pure1))

        drawing = [DrawSetPieceRule(), DrawPieceCMAPRule(), RedrawRule2(), SelectRule(),
                   MarkValidRule2(subruleset, move_start), SelectRule(), MarkCMAPRule(),
                   MarkRule2()]

        ruleset.add_all(special)
        ruleset.add_all(moves)
        ruleset.add_all(post_move)
        ruleset.add_all(actions)
        ruleset.add_all(drawing)

        start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
                "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"
    elif mode == "fairy":
        special = [CreatePieceRule({})]

        base_move = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
        piece_move = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

        move_constrs = base_move + piece_move
        move_start, moves, move_end = chain_rules(move_constrs, "move")
        moves += [SuccesfulMoveRule(move_end)]

        post_move = [MovedRule(), PromoteStartRule(["F"], ["J", "C", "S", "W"]),
                     PromoteReadRule(["J", "C", "S", "W"]),
                     WinRule()]

        actions = [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(), SetPieceRule(),
                   SetPlayerRule(), NextTurnRule(), WebTranslateRule(), ConnectRedrawRule(),
                   StatusRule(), LockRule(), WinStopRule()]

        # setup valid move marking
        pure_types = [[IdMoveRule], [FriendlyFireRule]] + piece_move  # pure moves (i.e. no side effects)
        pure0, pure, pure1 = chain_rules(pure_types, "move")

        subruleset = Ruleset(game)  # create new logic system
        subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

        subruleset.add_all(pure)
        subruleset.add_rule(SuccesfulMoveRule(pure1))

        drawing = [DrawSetPieceRule(), DrawPieceCMAPRule(), RedrawRule2(), SelectRule(),
                   MarkValidRule2(subruleset, move_start), SelectRule(), MarkCMAPRule(),
                   MarkRule2()]

        ruleset.add_all(special)
        ruleset.add_all(moves)
        ruleset.add_all(post_move)
        ruleset.add_all(actions)
        ruleset.add_all(drawing)

        start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;" \
                "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"
    else:
        return

    game.load_board_str(start)

    return game


class ServerState:
    def __init__(self):
        self.games = {}

    def run(self):
        start_server = websockets.serve(self.accept, "", 19683)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def do_room(self, room, mode, user, ws):
        print(room)

        if room not in self.games:
            chess = setup_chess(mode)
            chess.ruleset.add_rule(StopRule(self, room))
            self.games[room] = {"game": chess, "players": {}, "sockets": []}

        room_data = self.games[room]
        chess = room_data["game"]
        sockets = room_data["sockets"]

        sockets.append(ws)

        print(room_data)

        print(user)

        players = room_data["players"]
        if user in players:
            col = players[user]
        else:
            if len(players) == 0:
                col = "w"
            elif len(players) == 1:
                col = "b"
            else:
                col = "none"

        players[user] = col
        ws_rule = WebSocketRule(chess, col, ws)
        chess.ruleset.add_rule(ws_rule)
        await ws_rule.run()

    def close_room(self, room):
        try:
            room_data = self.games[room]

            for ws in room_data["sockets"]:
                ws.close()

            del self.games[room]
        finally:
            ...

    async def accept(self, ws: websockets.WebSocketServerProtocol, path):
        msg = await ws.recv()

        try:
            data = json.loads(msg)

            room, mode, user = data["room"], data["mode"], data["user"]

            room = room + "_" + mode
            await self.do_room(room, mode, user, ws)
        finally:
            ...


class ServerDaemon(Daemon):
    def __init__(self):
        Daemon.__init__(self, "game_daemon.pid")

        self.ss = None

    def run(self):
        self.ss = ServerState()
        self.ss.run()

    def cleanup(self):
        if self.ss:
            for room in self.ss.games:
                self.ss.close_room(room)


if __name__ == "__main__":
    ss = ServerState()
    ss.run()
