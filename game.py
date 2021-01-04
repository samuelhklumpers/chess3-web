from typing import List, Type

from line_of_sight_rules import *
from rules import *
from chess_rules import *
from normal_chess_rules import *
from fairy_rules import *
from chess_structures import *
from drawing_rules import *
from online import *
from structures import Ruleset


DRAWING_RULES: List[Rule] = [DrawInitRule(), RedrawRule(), MarkRule(), SelectRule(), MarkCMAPRule(), DrawPieceRule(), DrawPieceCMAPRule()]
MOVE_RULES: List[List[Type[Rule]]] = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
NETWORK_RULES: List[Rule] = [ReceiveRule(), CloseSocket()]


def make_actions(move_start: str):
    return [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(),
            SetPieceRule(), SetPlayerRule(), NextTurnRule(), CreatePieceRule()]


def make_online(chess: Chess, whitelist: List[Rule]):
    dialog = OnlineDialog(chess)
    addr, lport, rport, active = dialog.result
    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)
    rules = NETWORK_RULES + [SendRule(whitelist)]
    chess.ruleset.add_all(rules)


def setup_chess(config: dict, start_positions: str, piece_moves: List[List[Type[Rule]]], post_move: List[Rule], additional: List[Rule]):
    chess = Chess()  # make a blank board game instance
    ruleset = chess.ruleset

    moves = MOVE_RULES + piece_moves

    move0, move_rules, move1 = chain_rules(moves, "move")  # create conditional move chain
    move_rules += [SuccesfulMoveRule(move1)]  # add succesful move side effect

    actions = make_actions(move0)  # setup standard interactions (e.g. click, move, next turn)

    ruleset.add_all(move_rules)  # load rules
    ruleset.add_all(DRAWING_RULES)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)

    ruleset.add_rule(ExitRule(), -1)  # exit after every rule has processed "exit", ()

    ruleset.add_all(additional)  # load addons

    if config.get("show_valid", None) is not None:
        # mark all valid moves after clicking a piece, necessary for check/mate or Line of Sight
        show_valid: List[Type[Rule]] = config.get("show_valid")

        pure_types = [[IdMoveRule], [FriendlyFireRule]] + piece_moves  # pure moves (i.e. no side effects)
        pure0, pure, pure1 = chain_rules(pure_types, "move")

        subruleset = Ruleset(chess)  # create new logic system
        subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

        subruleset.add_all(pure)
        subruleset.add_rule(SuccesfulMoveRule(pure1))

        ruleset.add_rule(MarkValidRule(subruleset, pure0))  # add marker

        for rule_type in show_valid:
            rule = rule_type(subruleset, pure0)
            ruleset.add_rule(rule, 0)

    online = config.get("online", False)
    if not online and config.get("playback", ""):  # load game from playback
        ruleset.add_rule(PlaybackRule(chess, config["playback"], move0), 0)
    elif config.get("record", False):  # record playback
        ruleset.add_rule(RecordRule())

    chess.load_board_str(start_positions)  # load starting board

    if online:  # enable online functionality
        make_online(chess, [move1, "exit", "take", "create_piece"])

    ruleset.process("init", ())
    chess.geometry("600x600")
    return chess


def play_chess(online=True, playback="", record=True):
    move_rules= [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                  BishopRule, RookRule, QueenRule, KingRule, CastleRule]]  # add all normal chess moves

    post_move = [DrawSetPieceRule(), MovedRule(), PawnPostDouble(),
                 PromoteRule(["p"], ["L", "P", "T", "D"]), # special rules for pawn, rook and king
                 WinRule(), WinCloseRule()]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
            "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": []}

    chess = setup_chess(cfg, start, move_rules, post_move, additional)
    chess.mainloop()  # start the game


def play_fairy(online=True, playback="", record=True):
    move_rules = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

    post_move = [DrawSetPieceRule(),
                 PromoteRule(["F"], ["J", "C", "S", "W"]),
                 WinRule(), WinCloseRule()]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;"\
            "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": []}

    chess = setup_chess(cfg, start, move_rules, post_move, additional)
    chess.mainloop()  # start the game


def play_los(online=True, playback="", record=True):
    move_rules= [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                  BishopRule, RookRule, QueenRule, KingRule]]  # add all normal chess moves

    post_move = [MovedRule(), PawnPostDouble(),
                 PromoteRule(["p"], ["L", "P", "T", "D"]), # special rules for pawn, rook and king
                 WinRule(), WinCloseRule()]

    show_valid = [LineOfSightRule]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
            "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": show_valid}

    chess = setup_chess(cfg, start, move_rules, post_move, additional)
    chess.mainloop()  # start the game


if __name__ == '__main__':
    play_los(online=True, record=False)