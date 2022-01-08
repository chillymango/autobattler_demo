"""
Test Pokemon Factory, TM Manager, etc
"""
import mock
import unittest

from engine.player import EntityType, Player
from engine.pokemon import PokemonFactory
from engine.pokemon import TmManager


class TestPokemonFactory(unittest.TestCase):
    """
    Verify the PokemonFactory can be loaded
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]

    def setUp(self):
        # create a pokemonfactory
        PokemonFactory.CONFIG_PATH = "test/fixtures/test_default_movesets.txt"
        self.pokemon_factory = PokemonFactory(self.state)

    def test_load_default_movesets(self):
        self.assertEqual(len(self.pokemon_factory.default_movesets), 22)

    def test_get_default_battle_card(self):
        rattata = self.pokemon_factory.get_default_battle_card("rattata")
        # TODO: add better test
        self.assertEqual(rattata.name, 'rattata')

    def test_get_evolved_battle_card(self):
        """
        Create a shiny Pokemon and then attempt to apply evolution to it.
        Make sure the shiny flag persists.
        """
        pikachu = self.pokemon_factory.get_default_battle_card("pikachu")
        pikachu.shiny = True  # skip actual shiny power logic
        pikachu.tm_flag = True  # skip actual tm logic
        raichu = self.pokemon_factory.get_evolved_battle_card("raichu", pikachu)
        self.assertTrue(raichu.shiny)
        self.assertTrue(raichu.tm_flag)

    def test_create_pokemon_by_name(self):
        """
        Create two Pikachu. Verify they are not the same object.
        """
        pikachu1 = self.pokemon_factory.create_pokemon_by_name("pikachu")
        pikachu2 = self.pokemon_factory.create_pokemon_by_name("pikachu")
        self.assertEqual(pikachu1.name, "pikachu")
        self.assertEqual(pikachu2.name, "pikachu")
        self.assertNotEqual(pikachu1, pikachu2)


class TestTmManager(unittest.TestCase):
    """
    Verify the TM Manager works
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]

    def setUp(self):
        TmManager.CONFIG_PATH = "test/fixtures/test_tm_movesets.txt"
        self.tm_manager = TmManager(self.state)

    def test_initialize_tm_movesets(self):
        # verify default is "return" because why not
        self.assertEqual(self.tm_manager.get_tm_move("doesnotexist"), "RETURN")

    def test_example_tm_movesets(self):
        self.assertEqual(self.tm_manager.get_tm_move("pikachu"), "THUNDER")
        self.assertEqual(self.tm_manager.get_tm_move("raichu"), "THUNDER")
        self.assertEqual(self.tm_manager.get_tm_move("mewtwo"), "ZAP_CANNON")


if __name__ == "__main__":
    unittest.main()
