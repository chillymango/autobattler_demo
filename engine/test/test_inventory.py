"""
Test of the inventory manager
"""
import unittest

from engine.env import Environment
from engine.models.items import InstantPlayerItem
from engine.models.items import InstantPokemonItem
from engine.models.items import PersistentPlayerItem
from engine.models.items import PersistentPokemonItem
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.pokemon import EvolutionManager
from engine.pokemon import PokemonFactory
from engine.player import PlayerManager
from engine.items import ItemManager
from engine.inventory import PlayerInventoryManager

from engine.test.test_items import TEST_FACTORIES


class TestEnvironment(Environment):
    """
    Add inventory manager test utils

    Need to be able to support:
    * items
    * players
    * pokemon
    """

    @property
    def component_classes(self):
        return [
            ItemManager,
            PlayerManager,
            PokemonFactory,
            EvolutionManager,
            PlayerInventoryManager,
        ]


class TestCaseInventoryManager(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = TestEnvironment(8)
        # add players
        self.p1 = Player(name='Ima Human')
        self.p2 = Player(name='Harry Pottah')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.initialize()

        # add a pokemon
        poke_factory: PokemonFactory = self.env.pokemon_factory
        self.poke: Pokemon = poke_factory.create_pokemon_by_name("pikachu")

        # update factories
        im: ItemManager = self.env.item_manager
        for itemtype, factory in TEST_FACTORIES.items():
            im.import_factory(itemtype, factory)

    def test_something(self):
        """
        Just run a single case functional test
        """
        inv: PlayerInventoryManager = self.env.inventory

        # give a master ball to player 1 and verify his player master count increments
        test_item1: InstantPlayerItem = inv.create_and_give_item_to_player("test_master_ball", self.p1)
        self.assertTrue(test_item1 in self.p1.inventory)
        self.assertEqual(test_item1.holder, self.p1)
        test_item1.use()
        self.assertEqual(self.p1.master_balls, 5)

        # give a player an evo stone and a pokemon, give the item to a pokemon and use it
        test_item2: InstantPokemonItem = inv.create_and_give_item_to_player("test_evo_stone", self.p2)
        self.p2.add_to_party(self.poke)
        inv.give_item_to_pokemon(test_item2, self.poke)
        self.assertTrue(test_item2 not in self.p2.inventory)
        test_item2.use()
        self.assertEqual(self.poke.name, "raichu")

        # give an item to player1 and try to give it to player2's pokemon
        test_item3: PersistentPokemonItem = inv.create_and_give_item_to_player("test_xp_trinket", self.p1)
        with self.assertRaises(Exception):
            inv.give_item_to_pokemon(test_item3, self.poke)


if __name__ == "__main__":
    unittest.main()
