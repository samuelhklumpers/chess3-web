from structures.chess_structures import *


class RefChess(Chess):
    def __init__(self, chess: Chess):
        self.chess = chess

    def get_player(self):
        return self.chess.get_player()

    def get_turn(self):
        return self.chess.get_turn()

    def get_turn_num(self):
        return self.chess.get_turn_num()

    def get_id(self, obj):
        return self.chess.get_id(obj)

    def get_by_id(self, item_id: int):
        return self.chess.get_by_id(item_id)

    def get_board(self):
        return self.chess.get_board()


class NextTurnA(RefChess):
    def __init__(self, chess: RefChess):
        self.chess = chess

    def get_turn(self):
        return "w" if self.chess.get_turn() == "b" else "b"

    def get_turn_num(self):
        return self.chess.get_turn_num() + 1


class SetPieceTileA(NormalTile):
    def __init__(self, board: Board, tile: NormalTile, this_i, other_i, piece_id):
        self.board = board
        self.tile = tile
        self.this_i = this_i
        self.other_i = other_i
        self.piece_id = piece_id

    def get_piece(self):
        if self.this_i == self.other_i:
            piece = self.board.get_game().get_by_id(self.piece_id)
            return piece
        else:
            return self.tile.get_piece()


class SetPieceBoardA(Board):
    def __init__(self, chess: Chess, board: Board, tile_i, piece_id):
        self.chess = chess
        self.board = board
        self.tile_i = tile_i
        self.piece_id = piece_id

    def shape(self):
        return self.board.shape()

    def get_game(self):
        return self.chess

    def get_tile(self, tile_i):
        return SetPieceTileA(self, self.board.get_tile(tile_i), tile_i, self.tile_i, self.piece_id)


class SetPieceGameA(RefChess):
    def __init__(self, chess: Chess, tile_i, piece_id):
        self.chess = chess
        self.tile_i = tile_i
        self.piece_id = piece_id

    def get_board(self):
        return SetPieceBoardA(self, self.chess.get_board(), self.tile_i, self.piece_id)


__all__ = ["RefChess", "NextTurnA", "SetPieceTileA", "SetPieceBoardA", "SetPieceGameA"]