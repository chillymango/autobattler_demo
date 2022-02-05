"""
Set up a base case
"""
import typing as T
import unittest
from engine.battle import BattleManager

from engine.env import Environment
from engine.models.player import Player

from engine.models.association import PlayerInventory
from engine.models.association import PlayerRoster
from engine.models.association import PokemonHeldItem
from engine.models.items import Item
from engine.models.pokemon import Pokemon
from engine.player import PlayerManager


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

    def create_pokemon_with_item(
        self, 
        player: Player,
        pokemon_name: str,
        item_name: T.Optional[str] = None,
        level: int = 1,
    ):
        """
        Create a Pokemon and an item and give the item to the pokemon.
        """
        pm: PlayerManager = self.env.player_manager
        poke = pm.create_and_give_pokemon_to_player(player, pokemon_name)
        if item_name is not None:
            item = pm.create_and_give_item_to_player(player, item_name)
            item.level = level
            pm.give_item_to_pokemon(poke, item)

    def battle(self):
        # run battle between current two teams (p1 and p2) and return output dict
        bm: BattleManager = self.env.battle_manager
        return bm.battle(self.p1, self.p2)

    def _test_example(self):
        self.create_pokemon_with_item(self.p1, 'pikachu', 'IronBarb', level=3)
        self.create_pokemon_with_item(self.p2, 'raichu')
        self.create_pokemon_with_item(self.p2, 'snorlax', 'Leftovers', level=3)
        output = self.battle()
        # check this somehow idk

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
