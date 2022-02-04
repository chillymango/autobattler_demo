"""
Set up a base case
"""
import unittest

from engine.env import Environment
from engine.models.player import Player

from engine.models.association import PlayerInventory
from engine.models.association import PlayerRoster
from engine.models.association import PokemonHeldItem
from engine.models.items import Item
from engine.models.pokemon import Pokemon


class BaseEnvironmentTest(unittest.TestCase):
    """
    Create env and players
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(8)
        self.p1 = Player(name='Three Q')
        self.p2 = Player(name='Getta Name')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.initialize()

    def tearDown(self):
        # delete everything between tests...?
        super().tearDown()
        for inv in PlayerInventory.all():
            if inv:
                inv.delete()
        for ros in PlayerRoster.all():
            if ros:
                ros.delete()
        for item in PokemonHeldItem.all():
            if item:
                item.delete()
        for item_ in Item.all():
            if item_:
                item_.delete()
        for poke in Pokemon.all():
            if poke:
                poke.delete()
