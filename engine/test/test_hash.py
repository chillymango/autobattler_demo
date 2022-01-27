"""
What the fuck is going on
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory
from engine.shop import ShopManager
from engine.models.state import State


class TestGame(unittest.TestCase):
    """
    Test Game
    """

    def setUp(self):
        # create a new env
        self.env = Environment.create_webless_game(4)

    def test_whats_going_on(self):
        """
        Create a Pokemon and see why it's not hashing properly
        """
        self.p1 = Player(name="Balbert Bang")
        self.p2 = Player(name="Bill Yuan")
        self.p3 = Player(name="Tone Chenemdy")
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.add_player(self.p3)

        # start game
        self.env.initialize()

        # mess around
        pf: PokemonFactory = self.env.pokemon_factory
        for component in self.env.components:
            component.turn_setup()
        shop_manager: ShopManager = self.env.shop_manager
        for player in self.env.state.players:
            player.energy += 2
            shop_manager.roll(player)
            shop_manager.roll(player)
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 1)
            shop_manager.catch(player, 2)
            shop_manager.catch(player, 3)
            shop_manager.catch(player, 4)
            State.parse_raw(self.env.state.json())

        pm: PlayerManager = self.env.player_manager

