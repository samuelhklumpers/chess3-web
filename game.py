from typing import List, Type

from rules import *
from chess_rules import *
from normal_chess_rules import *
from fairy_rules import *
from chess_structures import *
from drawing_rules import *
from online import *


DRAWING_RULES = [DrawInitRule(), RedrawRule(), MarkRule(), SelectRule(), MarkCMAPRule(), DrawPieceRule(), DrawSetPieceRule(), DrawPieceCMAPRule()]
WIN_RULES = [WinRule(), WinCloseRule()]
COMMON_RULES = DRAWING_RULES + WIN_RULES

MOVE_RULES: List[List[Type[Rule]]] = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]

NETWORK_RULES = [ReceiveRule(), CloseSocket()]


def make_actions(move_start: str, move_finish: str):
    return [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(move_finish),
            SetPieceRule(), SetPlayerRule(), NextTurnRule()]


def make_online(chess: Chess, whitelist: List[Rule]):
    dialog = OnlineDialog(chess)
    addr, lport, rport, active = dialog.result

    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)

    rules = NETWORK_RULES + [SendRule(whitelist)]
    chess.ruleset.add_all(rules)


def play_chess(online=True, playback=""):
    chess = Chess()  # make a blank board game instance

    ruleset = chess.ruleset

    move_rules = MOVE_RULES + [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule, BishopRule,
                                RookRule, QueenRule, KingRule, CastleRule]]  # add all normal chess moves

    move0, move_rules, move1 = chain_rules(move_rules, "move")  # arrange the movement requirements
                                                                # in a chain of consequences
    actions = make_actions(move0, move1)  # setup normal user interactions
    actions += [DrawSetPieceRule()]

    post_move = [MovedRule(), PawnPostDouble()]  # special rules for pawn, rook and king

    ruleset.add_all(move_rules)  # load the rules
    ruleset.add_all(COMMON_RULES)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)
    if online:
        make_online(chess, [move1, "exit"])

    ruleset.add_rule(ExitRule(), -1)  # exit immediately on "exit", but after everything else processes the "exit"

    ruleset.add_rule(CreatePieceRule())  # necessary loading rule
    ruleset.add_rule(CounterRule())  # piece counter addon

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;"
                         "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")  # load pieces onto board

    if playback:
        ruleset.add_rule(PlaybackRule(chess, playback, move0), 0)
    else:
        ruleset.add_rule(RecordRule())

    ruleset.process("init", ())  # run initialization
    chess.geometry("600x600")
    chess.mainloop()  # start the game


def play_fairy_variant():
    chess = Chess()

    ruleset = chess.ruleset

    move_rules = MOVE_RULES + [[FighterRule, RiderRule, KirinRule, SniperRule, SquareRule, KingRule]]

    move0, move_rules, move1 = chain_rules(move_rules, "move")
    actions = [TouchMoveRule(move0), TakeRule(), MoveTakeRule(move1), SetPieceRule(), MoveRedrawRule(), NextTurnRule()]
    post_move = [MovedRule(), PawnPostDouble()]

    make_online(chess, [move0, "exit"])

    ruleset.add_all(move_rules)
    ruleset.add_all(COMMON_RULES)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)
    ruleset.add_rule(ExitRule(), -1)

    chess.load_board_str("wa8Sh8Sb8Rg8Rc8Cf8Cd8]e8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;ba1Sh1Sb1Rg1Rc1Cf1Cd1]e1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F")
    ruleset.process("init", ())
    chess.geometry("600x600")
    chess.mainloop()


if __name__ == '__main__':
    # play_chess(online=True)
    play_chess(online=False, playback="2020_12_30_13_05_48.chs")