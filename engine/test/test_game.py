"""
Setup and test an entire game
"""
import mock
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.player import PlayerManager
from engine.shop import ShopManager
from engine.models.state import State


class TestGame(unittest.TestCase):
    """
    Test Game
    """

    def setUp(self):
        # create a new env
        self.env = Environment.create_webless_game(8)

    def test_first_turn(self):
        """
        Runs loop manually

        First turn
        * add players
        * everyone buys the first 3 pokemon
        * initiate combat
        """
        state = self.env.state
        self.p1 = Player(name="Balbert Bang")
        self.p2 = Player(name="Bill Yuan")
        self.p3 = Player(name="Tone Chenemdy")
        self.p4 = Player(name="Ferry Jeng")
        self.p5 = Player(name='Meemsy Jiao')
        self.p6 = Player(name='Jay Zhang')
        self.p7 = Player(name='Pokemon Hater')
        self.p8 = Player(name='Pokemon Addict')
        for p in (self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8):
            self.env.add_player(p)

        # start game
        self.env.initialize()

        # step into game setup
        for component in self.env.components:
            component.turn_setup()

        # everyone rolls twice and then buys first 5 pokemon
        shop_manager: ShopManager = self.env.shop_manager
        for player in self.env.state.players:
            player.energy += 2
            shop_manager.roll(player)
            shop_manager.roll(player)
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 0)
            shop_manager.catch(player, 0)
            _ = State.parse_raw(self.env.state.json())

        # give someone a shiny for free
        player_manager: PlayerManager = self.env.player_manager
        player_manager.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        shop_manager.check_shiny(self.p1, 'pikachu')
        player_manager.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        shop_manager.check_shiny(self.p1, 'pikachu')
        player_manager.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        shop_manager.check_shiny(self.p1, 'pikachu')

        # everyone rolls again and buys their last 3 pokemon
        for player in self.env.state.players:
            player.energy += 2
            shop_manager.roll(player)
            shop_manager.catch(player, 4)
            shop_manager.catch(player, 3)
            _ = State.parse_raw(self.env.state.json())

        # everyone releases their second pokemon
        player_manager: PlayerManager = self.env.player_manager
        for player in self.env.state.players:
            poke: Pokemon = player_manager.player_party(player)[2]
            player_manager.release_pokemon(player, poke)

            _ = State.parse_raw(self.env.state.json())

        # step turn into combat
        for component in self.env.components:
            component.turn_execute()

        _ = State.parse_raw(self.env.state.json())

    @mock.patch('time.sleep')
    def test_with_game_loop(self, mock_sleep):
        """
        This sucks ass
        """
        self.p1 = Player(name="Balbert Bang")
        self.p2 = Player(name="Bill Yuan")
        self.p3 = Player(name="Tone Chenemdy")
        self.p4 = Player(name="Ferry Jeng")
        self.p5 = Player(name='Meemsy Jiao')
        self.p6 = Player(name='Jay Zhang')
        self.p7 = Player(name='Pokemon Hater')
        self.p8 = Player(name='Pokemon Addict')
        for p in (self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8):
            self.env.add_player(p)
        self.env.initialize()

        while True:
            try:
                self.env.step_loop()
            except Exception as exc:
                print(f'Encountered unexpected exception: {repr(exc)}')
                break
        print(len(self.env.state.json()))
