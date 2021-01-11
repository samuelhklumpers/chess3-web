import bisect
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
        self.size = 0
        self.rules = {}
        self.watches = {"all": []}
        self.lock = threading.RLock()

        self.debug = True

    def add_rule(self, rule, prio=1): # 0 first forbidden/debug, -1 last forbidden/debug
        self.rules.setdefault(prio, []).append(rule)

        if prio < 0:
            prio = 1000 - prio  # TODO

        for w in rule.watch:
            l = self.watches.setdefault(w, [])

            tup = (prio, self.size, rule)

            l.insert(bisect.bisect(l, tup), tup)

        self.size += 1

    def add_all(self, rules, prio=1):
        for rule in rules:
            self.add_rule(rule, prio=prio)

    def remove_rule(self, rule):
        for k in self.rules:
            if rule in self.rules[k]:
                self.rules[k].remove(rule)

        for w in rule.watch:
            if rule in self.watches.get(w, []):
                self.watches[w].remove(rule)

    def process_all(self, elist):
        try:
            for effect, args in elist:
                self.process(effect, args)
        except ValueError as e:
            raise e

    def process(self, effect, args):
        with self.lock:
            self._process(effect, args)

    def _process(self, effect, args):
        if self.debug:
            print(effect, args)

        views = self.watches.get(effect, []) + self.watches.get("all", [])
        views.sort()

        consequences = []
        prio2 = -1
        for prio, i, rule in views:
            if prio != prio2:
                prio2 = prio

                self.process_all(consequences)
                consequences = []

            res = rule.process(self.game, effect, args)

            if res:
                consequences += res

        self.process_all(consequences)

        """
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

            self.process_all(consequences)

        for k in late:
            consequences = []

            for rule in self.rules[k]:
                res = rule.process(self.game, effect, args)

                if res:
                    consequences += res

            self.process_all(consequences)"""


__all__ = ["Game", "TkGame", "Tile", "Ruleset"]