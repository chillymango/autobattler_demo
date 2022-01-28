"""
Item name enumeration encode / decode test
"""
import unittest

from engine.env import Environment
from engine.models.player import Player


class TestThisShit(unittest.TestCase):
    """
    ayy just encode some objects and deocde and check names
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='Freaking a')
        self.env.add_player(self.p1)
        self.env.initialize()

    def test_shit(self):
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
