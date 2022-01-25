"""
Test Player Manager, Models, Etc
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory


class TestPlayer(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='Xayah')
        self.p2 = Player(name='Rakan')
        self.p3 = Player(name='Kayle')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.add_player(self.p3)
        self.env.initialize()

    def test_party_config_interactions(self):
        """
        Give some Pokemon to each player, use some party config manipulation APIs, verify sanity
        of container outputs
        """
        pf: PokemonFactory = self.env.pokemon_factory
        pm: PlayerManager = self.env.player_manager

        # create pokemon
        pika = pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        rai = pm.create_and_give_pokemon_to_player(self.p1, 'raichu')
        mewtwo = pm.create_and_give_pokemon_to_player(self.p1, 'mewtwo')
        # check initial party and storage split
        self.assertEqual(len(pm.player_roster(self.p1)), 3)
        self.assertEqual(len(pm.player_party(self.p1)), 3)

        # create dupes for testing
        pika2 = pm.create_and_give_pokemon_to_player(self.p1, "pikachu")
        pika3 = pm.create_and_give_pokemon_to_player(self.p1, "pikachu")
        pika4 = pm.create_and_give_pokemon_to_player(self.p1, "pikachu")
        pika5 = pm.create_and_give_pokemon_to_player(self.p1, "pikachu")

        # check new party and storage split
        self.assertEqual(len(pm.player_party(self.p1)), 6)
        self.assertEqual(len(pm.player_storage(self.p1)), 1)

        # check team interactions
        self.p1.add_to_team_by_idx(0)
        self.assertEqual(len(pm.player_team(self.p1)), 1)


if __name__ == "__main__":
    unittest.main()
