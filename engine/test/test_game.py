"""
Setup and test an entire game
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.shop import ShopManager


class TestGame(unittest.TestCase):
    """
    Test Game
    """

    def setUp(self):
        # create a new env
        self.env = Environment.create_webless_game(4)

    def test_first_turn(self):
        """
        Runs loop manually

        First turn
        * add players
        * everyone buys the first 3 pokemon
        * initiate combat
        """
        p1 = Player(name="Balbert Bang")
        p2 = Player(name="Bill Yuan")
        p3 = Player(name="Tone Chenemdy")
        self.env.add_player(p1)
        self.env.add_player(p2)
        self.env.add_player(p3)

        # start game
        self.env.initialize()

        # step into game setup
        for component in self.env.components:
            component.turn_setup()

        # everyone buys first 3 pokemon
        for player in self.env.state.players:
            shop_manager: ShopManager = self.env.shop_manager
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 1)
            shop_manager.catch(player, 2)

        # step turn into combat
        for component in self.env.components:
            component.turn_execute()

        # can probably just end here
