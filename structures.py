import threading

import tkinter as tk


class Game:
    def __init__(self):
        self.ruleset = Ruleset(self)


class TkGame(tk.Tk):
    def __init__(self, game: Game):
        tk.Tk.__init__(self, "game")

        self.game = game


class Tile:
    ...


class Ruleset:
    def __init__(self, game: Game):
        self.game = game
        self.rules = {}
        self.lock = threading.RLock()

        self.debug = False

    def add_rule(self, rule, prio=1): # 0 first forbidden/debug, -1 last forbidden/debug
        self.rules.setdefault(prio, []).append(rule)

    def add_all(self, rules, prio=1):
        for rule in rules:
            self.add_rule(rule, prio=prio)

    def process_all(self, elist, prop=True):
        try:
            for effect, args in elist:
                self.process(effect, args, prop=prop)
        except ValueError as e:
            raise e

    def process(self, effect, args, prop=True):
        with self.lock:
            self._process(effect, args, prop=prop)

    def _process(self, effect, args, prop=True):
        if self.debug:
            print(effect, args)

        keys = list(self.rules.keys())

        early = [k for k in keys if k >= 0]
        late = [k for k in keys if k < 0]

        early.sort()
        late.sort()

        # make corecursive
        for k in early:
            consequences = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    consequences += res

            if prop:
                self.process_all(consequences)

        for k in late:
            consequences = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    consequences += res

            if prop:
                self.process_all(consequences)


__all__ = ["Game", "TkGame", "Tile", "Ruleset"]