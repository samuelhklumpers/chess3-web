from typing import List, Type

from rules.rules import *
from rules.lazy_rules import SetPieceRuleL, NextTurnRuleL
from rules.line_of_sight_rules import *
from rules.chess_rules import *
from rules.normal_chess_rules import *
from rules.fairy_rules import *
from rules.shogi_rules import *
from structures.chess_structures import *
from rules.drawing_rules import *
from utility.online import *
from structures.structures import *
from rules.network_rules import *

DRAWING_RULES: List[Rule] = [DrawInitRule(), RedrawRule(), MarkRule(), SelectRule(), MarkCMAPRule(), DrawPieceRule(),
                             DrawPieceCMAPRule()]
MOVE_RULES: List[List[Type[Rule]]] = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]
NETWORK_RULES: List[Rule] = [ReceiveRule("net0"), ColourRollRule("net0", "net1"), CloseSocket()]


def make_actions(move_start: str):
    return [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(),
            SetPieceRule(), SetPlayerRule(), WinMessageRule()]


def make_online(chess: Chess, whitelist: List[Rule]):
    dialog = OnlineDialog(chess.tkchess)
    addr, lport, rport, active = dialog.result
    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)
    rules = NETWORK_RULES + [SendRule(whitelist)]
    chess.ruleset.add_all(rules)


def setup_chess(config: dict, start_positions: str, special: List[Rule], piece_moves: List[List[Type[Rule]]],
                post_move: List[Rule], additional: List[Rule]):
    chess = Chess()  # make a blank board game instance

    board = Board(chess)
    board.make_tiles(NormalTile)
    chess.set_board(board)

    tkchess = TkChess(chess)
    tkchess.set_counter(PieceCounter())

    ruleset = chess.ruleset

    moves = MOVE_RULES + piece_moves
    late = [NextTurnRule()]

    ruleset.add_all(late, prio=-2)

    move0, move_rules, move1 = chain_rules(moves, "move")  # create conditional move chain
    has_check_rule = False
    if config.get("check",
                  None) is not None:  # warning dangerous experimental option, leaves the game in tie on checkmate, turns will take >1s to calculate
        win_cond = config["check"]

        lazy_set = Ruleset(chess)
        lazy_set.debug = False
        lazy_actions = [TakeRule(), MoveTakeRule(), SetPieceRuleL(), SetPlayerRule(), NextTurnRuleL()]

        lazy_set.add_all(move_rules + lazy_actions)
        lazy_set.add_rule(SuccesfulMoveRule(move1))
        lazy_set.add_rule(win_cond)

        check_rule = CheckRule(move1, "safe_move", move0, lazy_set)
        has_check_rule = True
        move_rules += [check_rule, SuccesfulMoveRule("safe_move")]
    else:
        move_rules += [SuccesfulMoveRule(move1)]  # add succesful move side effect

    actions = make_actions(move0)  # setup standard interactions (e.g. click, move, next turn)
    actions += special

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

        if has_check_rule:
            check_rule2 = CheckRule(pure1, "safe_move", pure0, lazy_set)
            pure1 = "safe_move"
            pure += [check_rule2]

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

    tkchess.geometry("600x600")
    return chess, tkchess


def play_chess(online=True, playback="", record=True):
    special = [CreatePieceRule({"K": MovedPiece, "p": Pawn, "T": MovedPiece})]

    move_rules = [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule,
                   BishopRule, RookRule, QueenRule, KingRule, CastleRule]]  # add all normal chess moves

    post_move = [DrawSetPieceRule(), MovedRule(), PawnPostDouble(),
                 PromoteRule(["p"], ["L", "P", "T", "D"]),  # special rules for pawn, rook and king
                 WinRule(), WinCloseRule()]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;" \
            "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": []}

    chess, tkchess = setup_chess(cfg, start, special, move_rules, post_move, additional)
    tkchess.mainloop()  # start the game


def play_fairy(online=True, playback="", record=True):
    special = [CreatePieceRule({})]

    move_rules = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

    post_move = [DrawSetPieceRule(),
                 PromoteRule(["F"], ["J", "C", "S", "W"]),
                 WinRule(), WinCloseRule()]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;" \
            "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": []}

    chess, tkchess = setup_chess(cfg, start, special, move_rules, post_move, additional)
    tkchess.mainloop()  # start the game


def play_los(online=True, playback="", record=True):
    special = [CreatePieceRule({})]

    move_rules = [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]

    post_move = [PromoteRule(["F"], ["J", "C", "S", "W"]),
                 WinRule(), WinCloseRule()]

    show_valid = [LineOfSightRule]

    additional = [CounterRule()]  # piece counter addon

    start = "wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;" \
            "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F"

    cfg = {"online": online, "playback": playback, "record": record, "show_valid": show_valid}

    chess, tkchess = setup_chess(cfg, start, special, move_rules, post_move, additional)
    tkchess.mainloop()  # start the game


def play_shogi(online=True, playback="", record=True):
    chess = Chess()
    board = Board(chess, 9, 9)
    board.make_tiles(NormalTile)
    chess.set_board(board)
    tkchess = TkChess(chess)

    ruleset = chess.ruleset

    special = [CreatePieceRule({})]

    move_rules = [[KingRule, SRookRule, DragonRule, SBishopRule, HorseRule, GoldRule,
                   SilverRule, PromotedSilverRule, CassiaRule, PromotedCassiaRule, Lance,
                   PromotedLanceRule, SoldierRule, PromotedSoldierRule]]

    post_move = [ShogiPromoteStartRule(), ShogiPromoteReadRule(),
                 WinRule(), WinCloseRule()]

    move_constrs = MOVE_RULES + move_rules
    move_start, moves, move_end = chain_rules(move_constrs, "move")
    moves += [SuccesfulMoveRule(move_end)]

    actions = make_actions(move_start)

    #
    pure_types = [[IdMoveRule], [FriendlyFireRule]] + move_rules  # pure moves (i.e. no side effects)
    pure0, pure, pure1 = chain_rules(pure_types, "move")

    subruleset = Ruleset(chess)  # create new logic system
    subruleset.debug = False  # beware, setting to True will often generate an unreadable amount of output

    subruleset.add_all(pure)
    subruleset.add_rule(SuccesfulMoveRule(pure1))

    ruleset.add_rule(MarkValidRule(subruleset, pure0))  # add marker
    #

    drawing = DRAWING_RULES + [DrawInitRule(), DrawSetPieceRule()]

    ruleset.add_all(special + moves + post_move + actions + drawing)

    late = [NextTurnRule()]
    ruleset.add_all(late, prio=-2)

    start = "wa9Lb9Nc9Sd9Ge9Kf9Gg9Sh9Ni9L" + "b8Bh8R" + "a7Pb7Pc7Pd7Pe7Pf7Pg7Ph7Pi7P;" \
            "ba1Lb1Nc1Sd1Ge1Kf1Gg1Sh1Ni1L" + "b2Rh2B" + "a3Pb3Pc3Pd3Pe3Pf3Pg3Ph3Pi3P"

    chess.load_board_str(start)
    chess.process("init", ())

    tkchess.geometry("600x600")
    tkchess.mainloop()


if __name__ == '__main__':
    play_shogi(online=False, playback="", record=False)
