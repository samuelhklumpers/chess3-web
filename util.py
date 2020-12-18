import itertools as itr
import numpy as np


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itr.zip_longest(*args, fillvalue=fillvalue)


def xyiter(x1, y1, x2, y2, incl_start=False, incl_end=False):
    sx = np.sign(x2 - x1)
    sy = np.sign(y2 - y1)

    if incl_start:
        yield x1, y1

    x1 += sx
    y1 += sy

    while not (sx != 0 and x1 == x2) and not (sy != 0 and y1 == y2):
        yield x1, y1

        x1 += sx
        y1 += sy

    if incl_end:
        yield x2, y2