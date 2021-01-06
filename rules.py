from typing import List

from structures import *


class Rule:
    def process(self, game: Game, effect: str, args):
        ...


class AnyRule(Rule):  # warning: ordering side effect
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def process(self, game: Game, effect: str, args):
        for rule in self.rules:
            elist = rule.process(game, effect, args)

            if elist:
                return elist


class IndicatorRule(Rule):
    def __init__(self, watch: List[str]):
        self.triggered = False
        self.watch = watch

    def set(self, v):
        self.triggered = v

    def unset(self):
        self.triggered = False

    def is_set(self):
        return self.triggered

    def process(self, game: Game, effect: str, args):
        if effect in self.watch:
            self.set(args or True)


def chain_rules(steps, base):
    rules = []
    out_effect = intro = base + "0"
    for i, step in enumerate(steps, start=1):
        in_effect = out_effect
        out_effect = base + str(i)

        for rule in step:
            inst = rule(in_effect, out_effect)
            rules.append(inst)

    return intro, rules, out_effect


def unpack2ddr(args):
        x1, y1 = args[0]
        x2, y2 = args[1]

        dx, dy = x2 - x1, y2 - y1

        return dx, dy


__all__ = ["Rule", "AnyRule", "IndicatorRule", "chain_rules", "unpack2ddr"]