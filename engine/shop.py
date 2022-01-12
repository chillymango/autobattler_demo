# py3
"""
Implements Shop Logic

TODO: fix private variable access into state._shop_window
"""
import os
import random
from collections import defaultdict
from collections import namedtuple

from engine.base import Component
from engine.pokemon import Pokemon, PokemonFactory
from engine.turn import Turn
from operator import attrgetter

# for debugging
SEED = os.environ.get("SHOP_RANDOM_SEED", 0)
#random.seed(SEED)
DEFAULT_SHOP_SIZE = 5


ShopCard = namedtuple("ShopCard", ["name", "tier", "encounter_score"])


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


class Shop:
    """
    A Shop should have a list of Pokemon that can be encountered, as well as
    their probabilities.

    This is exclusive to the backend. Frontend shop window rendering is done with
    a list of strings.
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


class ShopManager(Component):
    """
    Advance the shop. Config for the shop is stored here.
    """

    SHOP_TIERS_PATH = 'data/shop_tiers.txt'
    SHOP_DISTRIBUTION_PATH = 'data/shop_distribution.txt'
    SHOP_PROGRESSION_PATH = 'data/shop_progression.txt'

    def initialize(self):
        """
        Initialize shop manager and establish route
        """
        # load shop info
        with open(self.SHOP_TIERS_PATH, 'r') as shop_tiers_file:
            shop_tiers_raw = shop_tiers_file.readlines()
        self.pokemon_tier_lookup = {}
        for line in shop_tiers_raw:
            if not line:
                continue
            if line.startswith('#'):
                continue
            split = line.split()
            tier = int(split[0].strip())
            pokemon = split[1].strip()
            self.pokemon_tier_lookup[pokemon] = tier

        # load shop distribution
        with open(self.SHOP_DISTRIBUTION_PATH, 'r') as shop_distribution_file:
            shop_distribution_raw = shop_distribution_file.readlines()
        self.shop_distribution = []
        for line in shop_distribution_raw:
            self.shop_distribution.append([int(x) for x in line.split()])

        # load shop progression
        with open(self.SHOP_PROGRESSION_PATH, 'r') as shop_progression_file:
            shop_progression_raw = shop_progression_file.readlines()
        self.shop_progression = []
        for line in shop_progression_raw:
            if not line:
                continue
            if line.startswith('#'):
                continue
            self.shop_progression.append([int(x) for x in line.split(',')])

        # load shop tier colors
        # TODO: make this configurable
        self.tier_colors = defaultdict(lambda: "white")
        self.tier_colors.update(
            {1: "grey", 2: "green", 3: "blue", 4: "purple", 5: "orange", 6: "red"}
        )

    @property
    def route(self):
        """
        Dynamically load shop object based on the current turn
        """
        return {
            player: self.get_shop_by_turn_number(self.env.turn.number)
            for player in self.state.players
        }

    def get_pokemon_by_tier(self, tier):
        """
        Given a tier, return the Pokemon in that tier.
        """
        return [
            pokemon for pokemon, tier_ in self.pokemon_tier_lookup.items()
            if tier == tier_
        ]

    def get_distribution_by_turn_number(self, turn_number):
        """
        Given a turn number, generate the appropriate shop distribution

        Turn number is unit indexed, and so the index is shifted down 1.
        """
        if not turn_number:
            print("Invalid turn number {}".format(turn_number))
        stage = self.env.turn.stage
        return self.shop_distribution[stage.stage - 1]

    def get_shop_by_turn_number(self, turn_number):
        """
        Given a turn number, generate the appropriate shop
        """
        tiers = self.shop_progression[turn_number]
        distribution = self.get_distribution_by_turn_number(turn_number)
        shop_cards = []
        for tier in tiers:
            tier_idx = tier - 1
            pokemon = self.get_pokemon_by_tier(tier)
            shop_cards.extend(
                [ShopCard(name, tier, distribution[tier_idx]) for name in pokemon]
            )

        turn: Turn = self.env.turn
        stage = turn.get_stage_for_turn(turn_number)
        return Shop(stage.location, *shop_cards)

    def get_route_by_turn(self, turn):
        """
        Generates a route given a stage number.
        """
        # determine the stage based on the turn
        stage = self.turn_to_stage_lookup[turn]

        # determine max tier with distributions in it
        max_tier = max(self.shop_tiers[turn])

        # construct shop starting from lowest tier
        shop_cards = []
        for lower in range(0, max_tier):
            encounter_score = self.distribution[stage - 1][lower]  # holy shit indexing
            if not encounter_score:
                continue
            shop_cards.extend(
                [ShopCard(pokemon, encounter_score) for pokemon in self.pokemon_by_tier[lower + 1]]
            )

        return Shop("Stage {}".format(stage), *shop_cards)

    def turn_setup(self):
        """
        Load a new route for players based on the turn.
        """
        # load new shop for players who are alive
        for player in self.state.players:
            if player.is_alive:
                self.roll(player)
            else:
                self.state.shop_window_raw[player.id] = [None] * DEFAULT_SHOP_SIZE

    def catch(self, player, idx):
        """
        Catch the Pokemon at index in shop for player

        Do not refresh shop entry (leave as None).
        """
        card = self.state.shop_window[player][idx]
        cost = self.pokemon_tier_lookup[card]
        if cost > player.balls:
            print("Not enough Poke Balls to catch this Pokemon")
            return

        pokemon_factory: PokemonFactory = self.env.pokemon_factory
        caught = pokemon_factory.create_pokemon_by_name(self.state.shop_window[player][idx])
        player.add_to_roster(caught)
        player.balls -= cost
        self.state.shop_window_raw[player.id][idx] = None

        # shiny logic:
        # if there are three copies of a pokemon, combine them into a superset and mark it
        # as shiny
        # check here if there are already two non-shiny copies of a pokemon in a players
        # combined inventory
        pokemon_factory.shiny_checker(player,card)

    def roll(self, player):
        """
        Load a new shop for a player based on their route
        """
        if player.energy > 0:
            player.energy -= 1
            self.state.shop_window[player] = self.route[player].roll_shop()
        else:
            print("Cannot roll shop with no energy")
