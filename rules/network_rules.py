import threading
import random
import json
import traceback

from typing import List

from structures.chess_structures import *
from rules.rules import *


class ColourRollRule(Rule):
    def __init__(self, cause: str, consequence: str):
        self.cause = cause
        self.consequence = consequence

    def process(self, game: Chess, effect: str, args):
        if effect == self.cause:
            roll1 = random.getrandbits(64)
            game.socket.send(roll1.to_bytes(8, "big"))
            data = game.socket.recv(1024)
            roll2 = int.from_bytes(data, "big")

            if roll1 > roll2:
                player = "w"
            elif roll2 > roll1:
                player = "b"
            else:
                print("you win the lottery (1/2^128)")  # that's pretty impressive
                return [("exit", ())]

            return [("set_player", player), (self.consequence, ())]


class ReceiveRule(Rule):
    def __init__(self, network0):
        self.network0 = network0

    def run(self, game: Chess):
        try:
            game.receiving = True
            game.process(self.network0, ())
            game.receiving = False
            data = game.socket.recv(1024)
            game.receiving = True
            while data:
                for part in data.split(b";")[:-1]:
                    effect, args = json.loads(part.decode())

                    game.ruleset.process(effect, args)

                game.receiving = False
                data = game.socket.recv(1024)
                game.receiving = True
        except OSError:
            ...
        except:
            traceback.print_exc()

    def process(self, game: Chess, effect: str, args):
        if effect == "init":
            game.socket_thread = threading.Thread(target=lambda: self.run(game))
            game.socket_thread.start()


class SendRule(Rule):
    def __init__(self, whitelist: List[Rule]):
        self.whitelist = whitelist

    def process(self, game: Chess, effect: str, args):
        if not game.receiving:
            if effect in self.whitelist:
                game.socket.send(json.dumps((effect, args)).encode() + b";")


class CloseSocket(Rule):
    def process(self, game: Chess, effect: str, args):
        if effect == "exit":
            game.tkchess.after(1000, lambda: self.close(game))

    def close(self, game: Chess):
            try:
                game.socket.shutdown(0)
                game.socket.close()
            except:
                ...  # traceback.print_exc()

            if game.socket_thread.is_alive() and game.socket_thread != threading.current_thread():
                print("panic")


__all__ = ['ColourRollRule', 'ReceiveRule', 'SendRule', 'CloseSocket']