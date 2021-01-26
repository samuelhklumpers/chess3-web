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


class TouchCensorRule(Rule):
    def __init__(self, cons):
        Rule.__init__(self, watch=["touch"])
        self.cons = cons

    def process(self, game: Chess, effect: str, args):
        tile, player = args
        visible = game.get_board().get_views().get(player, {}).get("visible", set())

        if tuple(tile) in visible:
            return [(self.cons, args)]


class ServerLoSRule(Rule):
    def __init__(self, subruleset: Ruleset, move0):
        Rule.__init__(self, watch=["init", "turn_changed", "connect"])

        self.subruleset = subruleset
        self.move0 = move0

        self.success_indicator = IndicatorRule(["move_success"])
        self.subruleset.add_rule(self.success_indicator)

    def process(self, game: Chess, effect: str, args):
        if effect == "connect":
            view = game.get_board().get_views().get(args, None)

            if view:
                res = [("set_filter", args)]
                for tile in view["visible"]:
                    res += [("draw_piece", tile)]
                for tile in view["invisible"]:
                    res += [("overlay", (tile, "#", HEXCOL["fog"])), ("draw_piece_at2", (tile, "", HEXCOL[args]))]
                res += [("set_filter", "all")]
                return res

        if effect in ["init", "turn_changed"]:
            board = game.board
            views = board.get_views()

            pieces, visible, invisible = {}, {}, {}

            tiles = list(board.tile_ids())
            for tile in tiles:
                piece = board.get_tile(tile).get_piece()

                if piece:
                    player = piece.get_colour()
                    pieces.setdefault(player, []).append((tile, piece))
                    visible.setdefault(player, set()).add(tile)

            for tile in tiles:
                for player in pieces:
                    if tile in visible.get(player, ()) or tile in invisible.get(player, ()):
                        continue

                    can_see = False
                    for start, piece in pieces[player]:
                        can_see = is_valid(self.success_indicator, self.move0, self.subruleset, start, tile)
                        if can_see:
                            visible.setdefault(player, set()).add(tile)
                            break

                    if not can_see:
                        invisible.setdefault(player, set()).add(tile)

            elist = []
            for player in visible:
                visible_p, invisible_p = visible[player], invisible[player]

                elist += [("set_filter", player)]
                for tile in visible_p:
                    elist += [("draw_piece", tile)]
                for tile in invisible_p:
                    elist += [("draw_piece_at2", (tile, "", HEXCOL[player]))]

                view = views.setdefault(player, {"visible": set(), "invisible": set()})
                became_visible = view["invisible"].intersection(visible_p)
                became_invisible = view["visible"].intersection(invisible_p)

                for tile in became_visible:
                    elist += [("overlay", (tile, "", HEXCOL["fog"]))]
                for tile in became_invisible:
                    elist += [("overlay", (tile, "#", HEXCOL["fog"]))]

                view["visible"] = visible_p
                view["invisible"] = invisible_p
            elist += [("set_filter", "all")]

            return elist


__all__ = ['LineOfSightRule', 'ServerLoSRule', 'TouchCensorRule']
