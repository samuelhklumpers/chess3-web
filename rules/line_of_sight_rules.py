from structures.chess_structures import *
from rules.rules import *
from structures.structures import *
from structures.colours import *


class LineOfSightRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        Rule.__init__(self, watch=["move_success", "turn_changed"])

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


def is_valid(indicate, move0, ruleset, start, end):
    indicate.unset()
    ruleset.process(move0, (start, end))
    ret = indicate.is_set()
    indicate.unset()
    return ret


class ServerLoSRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        Rule.__init__(self, watch=["turn_changed"])

        self.subruleset = subruleset
        self.move0 = move0

        self.success_indicator = IndicatorRule(["move_success"])
        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == "turn_changed":
            board = game.board
            pieces = {}
            visible = {}
            invisible = {}
            for tile_id in board.tile_ids():
                piece = board.get_tile(tile_id).get_piece()

                if piece:
                    player = piece.get_colour()
                    pieces.setdefault(player, []).append((tile_id, piece))
                    visible.setdefault(player, set()).add(tile_id)

            for tile_id in board.tile_ids():
                for player in pieces:
                    if tile_id in visible.get(player, ()) or tile_id in invisible.get(player, ()):
                        continue

                    valid = False
                    for start, piece in pieces[player]:
                        valid = is_valid(self.success_indicator, self.move0, self.subruleset, start, tile_id)
                        if valid:
                            visible.setdefault(player, set()).add(tile_id)
                            break

                    if not valid:
                        invisible.setdefault(player, set()).add(tile_id)

            elist = []
            for player in visible:
                elist += [("set_filter", player)]

                for tile in visible[player]:
                    elist += [("draw_piece", tile), ("overlay", (tile, "", HEXCOL["valid"]))]

                for tile in visible[player]:
                    elist += [("draw_piece_at2", (tile, "", HEXCOL[player])),
                              ("overlay", (tile, "#", HEXCOL["fog"]))]

            elist += [("set_filter", "all")]
            print(elist)
            print(pieces)
            print(visible)
            print(invisible)
            return elist


__all__ = ['LineOfSightRule', 'ServerLoSRule']
