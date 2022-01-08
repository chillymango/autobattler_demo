"""
Test the shop generation utilities
"""
import mock
import random
import unittest

from engine.player import EntityType
from engine.player import Player
from engine.shop import Shop
from engine.shop import ShopCard
from engine.shop import ShopManager
from engine.turn import Turn


class TestShop(unittest.TestCase):
    """
    Test Shop Function
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]
        random.seed(0)

    def setUp(self):
        self.pokemon = [
            ShopCard("pikachu", 3, 1.0),
            ShopCard("mewtwo", 5, 1.0),
        ]

    def test_shop_simple(self):
        shop = Shop("test shop", *self.pokemon)
        results = shop.roll_shop()
        self.assertListEqual(results, ['mewtwo', 'mewtwo', 'pikachu', 'pikachu', 'mewtwo'])


class TestShopManager(unittest.TestCase):
    """
    Test Shop Manager
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]

        # add / initialize stuff required to run the shop manager
        cls.state.turn = Turn(cls.state)
        cls.state.turn.advance()

    def setUp(self):
        ShopManager.SHOP_TIERS_PATH = "test/fixtures/test_shop_tiers.txt"
        self.shop_manager = ShopManager(self.state)

    def test_init(self):
        self.assertEqual(len(self.shop_manager.pokemon_tier_lookup), 10)
        self.assertEqual(len(self.shop_manager.get_pokemon_by_tier(6)), 2)

    def test_shop_creation(self):
        shop = self.shop_manager.get_shop_by_turn_number(1)
        self.assertEqual(len(shop.roll_shop()), 5)


if __name__ == "__main__":
    unittest.main()
