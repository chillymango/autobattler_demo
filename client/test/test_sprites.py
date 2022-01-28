"""
Initialize and verify
"""
import unittest

from client.client_env import ClientEnvironment
from engine.models.player import Player


class TestSpriteManager(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = ClientEnvironment(4)
        self.p1 = Player(name='Balbsbert Bang')
        self.env.add_player(self.p1)

    def test_initialize(self):
        self.env.initialize()
        import IPython; IPython.embed()

if __name__ == "__main__":
    unittest.main()
