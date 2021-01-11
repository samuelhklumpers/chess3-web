from rules.rules import *
from structures.lazy_structures import *


class SetPieceRuleL(Rule):
    def process(self, game: RefChess, effect: str, args):
        if effect == "set_piece":
            tile_i, piece_id = args[0], args[1]

            game.chess = SetPieceGameA(game.chess, tile_i, piece_id)

            return [("piece_set", args)]


class NextTurnRuleL(Rule):
    def process(self, game: RefChess, effect: str, args):
        if effect == "moved":
            game.chess = NextTurnA(game.chess)

            return [("turn_changed", ())]


__all__ = ["SetPieceRuleL", "NextTurnRuleL"]