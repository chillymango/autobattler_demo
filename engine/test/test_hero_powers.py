import typing as T
import unittest

from engine.env import Environment
from engine.models.player import Player


class TestHeroPowerEffects(unittest.TestCase):
    """
    Setup game and make sure hero effects fuckin work
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='bassf s')
        self.env.add_player(self.p1)

    def test_bruno_bod(self):
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
