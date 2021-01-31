import numpy as np

from utility.util import *


def forward(game, args):
    dx, dy = unpack2ddr(args)
    c = game.get_board().get_tile(args[0]).get_piece().get_colour()
    d = 1 if c == "b" else -1

    if np.sign(dy) == d:
        return args


def wazir(args):
    dx, dy = unpack2ddr(args)

    if abs(dx) + abs(dy) == 1:
        return args


def ferz(args):
    dx, dy = unpack2ddr(args)

    if abs(dx * dy) == 1:
        return args


def rook(game, args):
    x1, y1 = args[0]
    x2, y2 = args[1]
    dx, dy = unpack2ddr(args)

    b = game.get_board()

    if dx * dy == 0 and not any(b.get_tile(x).get_piece() for x in xyiter(x1, y1, x2, y2)):
        return args


def bishop(game, args):
    x1, y1 = args[0]
    x2, y2 = args[1]
    dx, dy = unpack2ddr(args)

    b = game.get_board()

    if abs(dx) == abs(dy) and not any(b.get_tile(x).get_piece() for x in xyiter(x1, y1, x2, y2)):
        return args


def knight(args):
    dx, dy = unpack2ddr(args)

    if abs(dx * dy) == 2 and abs(dy) == 2:
        return args
