"""
Test party configuration shit
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.player import PlayerManager

class TestPartyConfig(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='SLANDER')
        self.p2 = Player(name='William Black')
        self.p3 = Player(name='The Weeknd')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.add_player(self.p3)
        self.env.initialize()

    def test_party_config(self):
        """
        Give some Pokemon, manipulate party config, verify it looks right
        """
        state = self.env.state
        # add a few pokemon to the party and then populate the team using autopop
        pm: PlayerManager = self.env.player_manager
        pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        pm.create_and_give_pokemon_to_player(self.p1, 'raichu')
        pm.create_and_give_pokemon_to_player(self.p1, 'mewtwo')
        pm.create_and_give_pokemon_to_player(self.p1, 'dratini')
        party = pm.player_party(self.p1)
        team = pm.player_team(self.p1)
        self.assertEqual(len(party), 4)
        self.assertEqual(len(team), 0)
        self.p1.party_config.populate_team_from_party()
        team = pm.player_team(self.p1)
        self.assertEqual(len(team), 3)


if __name__ == "__main__":
    unittest.main()
