"""
I'm really bad at math / programming so lets manually
do some speed calculations / operations
"""
import unittest
from engine.test.base import BaseEnvironmentTest


class TestSpeedItems(BaseEnvironmentTest):

    def test_speed_items(self):
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
