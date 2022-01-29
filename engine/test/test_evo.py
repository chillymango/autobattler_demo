"""
Test Evolutions
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory


class TestEvolutions(unittest.TestCase):
    
    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='chilly mango')
        self.env.add_player(self.p1)

    def test_evolution_function(self):
        self.env.initialize()
        pm: PlayerManager = self.env.player_manager
        pika = pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        for turn in range(5):
            for component in self.env.components:
                component.turn_setup()
                component.turn_cleanup()

        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
