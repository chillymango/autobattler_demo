# py3
"""
Implements Shop Logic
"""
import os
import random
from collections import defaultdict
from collections import namedtuple
from uuid import uuid4

from engine.base import Component
from engine.pokemon import Pokemon

# for debugging
SEED = os.environ.get("SHOP_RANDOM_SEED", 0)
random.seed(SEED)
DEFAULT_SHOP_SIZE = 5


ShopCard = namedtuple("ShopCard", ["name", "encounter_score"])

COST_LOOKUP = defaultdict(
    lambda: 5
)
COST_LOOKUP.update(dict(
    pidgey=1,
    rattata=1,
))


class Interval:
    """
    Util class that stores interval data and supports basic operations
    """

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def in_range(self, val, strict=False):
        if strict:
            return val > self.lower and val < self.upper
        return val >= self.lower and val <= self.upper


class Route:
    """
    A Route should have a list of Pokemon that can be encountered, as well as
    their probabilities.
    """

    def __init__(self, name, *pokemon):
        self.name = name
        self.cards = pokemon
        self._prob = 0.0
        for card in self.cards:
            self._prob += card.encounter_score

        if abs(self._prob - 1.0 > 1E8):  # floating point error lmfao
            print("Warning: encounter scores sum to {} on {}".format(self._prob, self.name))

        self._intervals = []
        _prev = 0.0
        for card in self.cards:
            _next = _prev + card.encounter_score / self._prob
            self._intervals.append((card.name, Interval(_prev, _next)))
            _prev = _next

    def roll_shop(self, shop_size=DEFAULT_SHOP_SIZE):
        """
        Draw a number of cards from the Route shop using the probabilities provided.

        A shop is populated by generating a list of random numbers that matches the
        shop_size. Depending on which intervals these numbers fall into, a Pokemon
        will be selected.
        """
        shop = []
        randoms = [random.random() for _ in range(shop_size)]
        for val in randoms:
            for pokemon, interval in self._intervals:
                if interval.in_range(val):
                    shop.append(pokemon)
                    break

        return shop


route1 = Route(
    "Route 1",
    ShopCard("rattata", 0.30),
    ShopCard("pidgey", 0.70),
)

route2 = Route(
    "Route 2",
    ShopCard("pidgey", 0.34),
    ShopCard("rattata", 0.35),
    ShopCard("nidoranf", 0.15),
    ShopCard("nidoranm", 0.15),
    ShopCard("mrmime", 0.01)
)

route3 = Route(
    "Route 3",
    ShopCard("rattata", 0.15),
    ShopCard("spearow", 0.55),
    ShopCard("sandshrew", 0.15),
    ShopCard("mankey", 0.15)
)

route4 = Route(
    "Route 4",
    ShopCard("rattata", 0.10),
    ShopCard("spearow", 0.45),
    ShopCard("sandshrew", 0.05),
    ShopCard("mankey", 0.05),
    ShopCard("magikarp", 0.15),
    ShopCard("psyduck", 0.10),
    ShopCard("goldeen", 0.10),
)


class ShopManager(Component):
    """
    Advance the shop. Config for the shop is stored here.
    """

    def initialize(self, start=route1):
        """
        Initialize shop manager and establish route
        """
        self.shop = {player: [None] * DEFAULT_SHOP_SIZE for player in self.state.players}
        self.route = {player: start for player in self.state.players}
        # use a fixed progression for now, maybe add advanced logic later
        self.progression = defaultdict(lambda: route4)
        self.progression.update({
            1: route1,
            2: route2,
            3: route3,
            4: route4,
        })

    def turn_setup(self):
        """
        Load a new route for players based on the turn.
        """
        turn = self.state.turn
        self.route = {player: self.progression[turn] for player in self.state.players}

        # load new shop for players who are alive
        for player in self.state.players:
            if player.is_alive:
                self.roll(player)
            else:
                self.shop[player] = [None] * DEFAULT_SHOP_SIZE

    def catch(self, player, idx):
        """
        Catch the Pokemon at index in shop for player

        Do not refresh shop entry (leave as None).
        """
        card = self.shop[player][idx]
        cost = COST_LOOKUP[card]
        if cost > player.balls:
            raise ValueError("Not enough Poke Balls to catch this Pokemon")

        caught = Pokemon(self.shop[player][idx])
        player.add_to_roster(caught)
        player.balls -= cost
        self.shop[player][idx] = None

    def roll(self, player):
        """
        Load a new shop for a player based on their route
        """
        self.shop[player] = self.route[player].roll_shop()


if __name__ == "__main__":
    print("Welcome to the shop (route 4)")
    print("Press Enter to roll new values")
    while True:
        input("\n")
        print(route4.roll_shop())
