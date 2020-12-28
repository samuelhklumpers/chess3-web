from structures import Game


class Rule:
    def process(self, game: Game, effect: str, args):
        ...


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


__all__ = ["Rule", "chain_rules", "unpack2ddr"]