import mock
import unittest

from engine.player import EntityType
from engine.player import Player
from engine.turn import Turn

FIRST_TURN = 1
LAST_TURN = 21


class TestStageLoad(unittest.TestCase):
    """
    Load stage information and verify valid turn association
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]

    def setUp(self):
        Turn.CONFIG_PATH = "test/fixtures/test_stages.txt"
        self.turn = Turn(self.state)

    def test_stage_load(self):
        self.assertEqual(min(self.turn.stages.keys()), FIRST_TURN)
        self.assertEqual(max(self.turn.stages.keys()), LAST_TURN)

        # verify it starts uninitialized
        self.assertIsNone(self.turn.stage)

    def test_advance_turn(self):
        """
        Execute advancing actions
        """
        self.turn.advance()
        self.assertEqual(self.turn.number, FIRST_TURN)
        self.assertEqual(self.turn.stage.stage, 1)
        self.assertEqual(self.turn.stage.round, 1)

        self.turn.advance()
        self.assertEqual(self.turn.number, FIRST_TURN + 1)
        self.assertEqual(self.turn.stage.stage, 1)
        self.assertEqual(self.turn.stage.round, 2)


if __name__ == "__main__":
    unittest.main()
