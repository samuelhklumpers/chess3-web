from typing import List, Type

from rules import *
from chess_rules import *
from normal_chess_rules import *
from fairy_rules import *
from chess_structures import *
from drawing_rules import *
from online import *
from structures import Ruleset

DRAWING_RULES = [DrawInitRule(), RedrawRule(), MarkRule(), SelectRule(), MarkCMAPRule(), DrawPieceRule(), DrawSetPieceRule(), DrawPieceCMAPRule()]
WIN_RULES = [WinRule(), WinCloseRule()]
COMMON_RULES = DRAWING_RULES + WIN_RULES

MOVE_RULES: List[List[Type[Rule]]] = [[IdMoveRule], [MoveTurnRule], [MovePlayerRule], [FriendlyFireRule]]

NETWORK_RULES = [ReceiveRule(), CloseSocket()]


def make_actions(move_start: str):
    return [TouchMoveRule(move_start), TakeRule(), MoveTakeRule(),
            SetPieceRule(), SetPlayerRule(), NextTurnRule()]


def make_online(chess: Chess, whitelist: List[Rule]):
    dialog = OnlineDialog(chess)
    addr, lport, rport, active = dialog.result

    sock = make_socket(addr, lport, rport, active)

    chess.set_socket(sock)

    rules = NETWORK_RULES + [SendRule(whitelist)]
    chess.ruleset.add_all(rules)


def play_chess(online=True, playback="", record=True):
    chess = Chess()  # make a blank board game instance

    ruleset = chess.ruleset

    move_rules = MOVE_RULES + [[PawnSingleRule, PawnDoubleRule, PawnTakeRule, PawnEnPassantRule, KnightRule, BishopRule,
                                RookRule, QueenRule, KingRule, CastleRule]]  # add all normal chess moves

    move0, move_rules, move1 = chain_rules(move_rules, "move")  # arrange the movement requirements
                                                                # in a chain of consequences
    move_rules += [SuccesfulMoveRule(move1)]
    actions = make_actions(move0)  # setup normal user interactions
    actions += [DrawSetPieceRule()]

    post_move = [MovedRule(), PawnPostDouble(),
                 PromoteRule(["p"], ["L", "P", "T", "D"])]  # special rules for pawn, rook and king

    ruleset.add_all(move_rules)  # load the rules
    ruleset.add_all(COMMON_RULES)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)

    ruleset.add_rule(ExitRule(), -1)  # exit immediately on "exit", but after everything else processes the "exit"

    ruleset.add_rule(CreatePieceRule())  # necessary loading rule
    ruleset.add_rule(CounterRule())  # piece counter addon

    chess.load_board_str("wa8Th8Tb8Pg8Pc8Lf8Ld8De8Ka7pb7pc7pd7pe7pf7pg7ph7p;"
                         "ba1Th1Tb1Pg1Pc1Lf1Ld1De1Ka2pb2pc2pd2pe2pf2pg2ph2p")  # load pieces onto board

    if online:
        make_online(chess, [move1, "exit", "take", "create_piece"])
    elif playback:
        ruleset.add_rule(PlaybackRule(chess, playback, move0), 0)

    if not playback and record:
        ruleset.add_rule(RecordRule())

    ruleset.process("init", ())  # run initialization
    chess.geometry("600x600")
    chess.mainloop()  # start the game


def play_fairy_variant(online=True, playback="", record=True):
    chess = Chess()

    ruleset = chess.ruleset

    move_rules = MOVE_RULES + [[FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]
    move0, move_rules, move1 = chain_rules(move_rules, "move")

    move_rules += [SuccesfulMoveRule(move1)]

    actions = make_actions(move0)
    actions += [DrawSetPieceRule()]

    post_move = [MovedRule(), PawnPostDouble(),
                 PromoteRule(["F"], ["J", "C", "S", "W"])]
    ruleset.add_all(move_rules)
    ruleset.add_all(COMMON_RULES)
    ruleset.add_all(actions)
    ruleset.add_all(post_move)

    ruleset.add_rule(ExitRule(), -1)

    ruleset.add_rule(CreatePieceRule())
    ruleset.add_rule(CounterRule())

    turnless = [[IdMoveRule], [FriendlyFireRule], [FerzRule, JumperRule, KirinRule, ShooterRule, WheelRule, KingRule]]
    turnless0, turnless_rules, turnless1 = chain_rules(turnless, "move")

    subruleset = Ruleset(chess)
    subruleset.add_all(turnless_rules)
    subruleset.add_rule(SuccesfulMoveRule(turnless1))
    ruleset.add_rule(MarkValidRule(subruleset, turnless0))

    chess.load_board_str("wa8Sh8Sb8Jg8Jc8Cf8Cd8We8Ka7Fb7Fc7Fd7Fe7Ff7Fg7Fh7F;"
                         "ba1Sh1Sb1Jg1Jc1Cf1Cd1We1Ka2Fb2Fc2Fd2Fe2Ff2Fg2Fh2F")

    if online:
        make_online(chess, [move1, "exit", "take", "create_piece"])
    elif playback:
        ruleset.add_rule(PlaybackRule(chess, playback, move0), 0)

    if not playback and record:
        ruleset.add_rule(RecordRule())

    ruleset.process("init", ())
    chess.geometry("600x600")
    chess.mainloop()


if __name__ == '__main__':
    play_fairy_variant(online=False, record=False)
    # play_chess(record=False, online=False)
    # play_chess(online=True, record=False)
    # play_chess(online=False, playback="2020_12_30_13_05_48.chs")