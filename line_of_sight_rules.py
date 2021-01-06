from chess_structures import *
from rules import *
from structures import *
from colours import *


class LineOfSightRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        self.subruleset = subruleset
        self.move0 = move0

        self.success_indicator = IndicatorRule(["move_success"])
        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == "move_success":
            elist = []

            board = game.board
            tkboard = board.tkboard

            for tile_id in board.tile_ids():
                tag = tkboard.tile_tags[tile_id]
                tkboard.itemconfig(tag, fill=HEXCOL["fog"])
                elist += [("draw_piece_at", (tile_id, "", ""))]

            return elist

        if effect == "turn_changed":
            to_draw = set()

            board = game.board
            tkboard = board.tkboard

            for tile_id in board.tile_ids():
                tile = board.get_tile(tile_id)
                piece = tile.get_piece()

                if piece and piece.get_colour() in game.player:
                    to_draw.add(tile_id)

                    for valid in search_valid(self, game, around=tile_id):
                        to_draw.add(valid)

            elist = []
            for tile_id in to_draw:
                tag = tkboard.tile_tags[tile_id]

                i, j = tile_id
                parity = (i + j) % 2
                col = HEXCOL["tile_white"] if parity else HEXCOL["tile_brown"]

                tkboard.itemconfig(tag, fill=col)
                elist += [("draw_piece", tile_id)]

            return elist


__all__ = ['LineOfSightRule']