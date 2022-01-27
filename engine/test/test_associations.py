"""
wow I feel like this is close
"""
import unittest
from engine.models.association import associate
from engine.models.association import dissociate
from engine.models.association import PlayerRoster
from engine.env import Environment
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.pokemon import PokemonFactory


class TestAssociations(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='SLANDER')
        self.p2 = Player(name='Illenium')
        self.p3 = Player(name='William Black')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.add_player(self.p3)
        self.env.initialize()

    def test_association(self):
        pf: PokemonFactory = self.env.pokemon_factory
        pika = pf.create_pokemon_by_name('pikachu')
        rai = pf.create_pokemon_by_name('raichu')
        mewtwo = pf.create_pokemon_by_name('mewtwo')
        associate(PlayerRoster, self.p1, pika)
        associate(PlayerRoster, self.p1, rai)
        associate(PlayerRoster, self.p2, mewtwo)
        self.assertEqual(len(PlayerRoster.get_roster(self.p1)), 2)
        self.assertEqual(len(PlayerRoster.get_roster(self.p2)), 1)


if __name__ == "__main__":
    unittest.main()
