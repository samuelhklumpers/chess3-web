from chess_structures import *
from drawing_rules import *
from rules import *
from structures import *


class LineOfSightRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        self.subruleset = subruleset
        self.move0 = move0

        self.success_indicator = IndicatorRule(["move_success"])
        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == "move_success":
            elist = []

            for tile_id in game.board.tile_ids():
                tag = game.board.tile_tags[tile_id]
                game.board.itemconfig(tag, fill="#444444")
                elist += [("draw_piece_at", (tile_id, "", ""))]

            return elist

        if effect == "turn_changed":
            to_draw = set()

            for tile_id in game.board.tile_ids():
                tile = game.board.get_tile(tile_id)
                piece = tile.get_piece()

                if piece and piece.get_colour() in game.player:
                    to_draw.add(tile_id)

                    for valid in search(self, game, around=tile_id):
                        to_draw.add(valid)

            elist = []
            for tile_id in to_draw:
                tag = game.board.tile_tags[tile_id]

                i, j = tile_id
                parity = (i + j) % 2
                col = '#E2DA9C' if parity else '#AF8521'

                game.board.itemconfig(tag, fill=col)
                elist += [("draw_piece", tile_id)]

            return elist


__all__ = ['LineOfSightRule']