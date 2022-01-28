"""
Test party configuration shit
"""
import unittest

from engine.env import Environment
from engine.models.player import Player

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
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
