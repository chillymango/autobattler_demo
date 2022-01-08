"""
Matchmaker Tests
"""
import mock
import random
import unittest

from engine.match import CreepRoundManager
from engine.match import Match
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player


class TestMatchLogic(unittest.TestCase):
    """
    Basic tests for the `Match` object go here
    """

    @classmethod
    def setUpClass(cls):
        super(TestMatchLogic, cls).setUpClass()
        cls.players = [
            Player('Ashe Ketchum', type_=EntityType.HUMAN),
            Player('Red Dawn', type_=EntityType.COMPUTER),
            Player('Blue Steel', type_=EntityType.COMPUTER),
        ]

    def test_has_player(self):
        match = Match(self.players[0], self.players[1])
        self.assertTrue(match.has_player(self.players[0]))
        self.assertTrue(match.has_player(self.players[1]))
        self.assertFalse(match.has_player(self.players[2]))


class TestMatchmakerUtils(unittest.TestCase):
    """
    Mock out the test history and verify that the util functions for match history
    are valid.
    """

    def setUp(self):
        p1 = Player("Albert Yang", type_=EntityType.HUMAN)
        p2 = Player("William Yuan", type_=EntityType.HUMAN)
        p3 = Player("Anthony Chen", type_=EntityType.HUMAN)
        p4 = Player("Jerry Feng", type_=EntityType.HUMAN)
        p5 = Player("Mimi Jiao", type_=EntityType.HUMAN)
        p6 = Player("Ligma", type_=EntityType.COMPUTER)
        p7 = Player("BlazeIt", type_=EntityType.COMPUTER)
        p8 = Player("MewThree", type_=EntityType.COMPUTER)
        humans = [p1, p2, p3, p4, p5]
        computers = [p6, p7, p8]
        self.players = humans + computers
        state = mock.MagicMock()
        state.players = self.players
        self.matchmaker = Matchmaker(state)

    def test_previous_round_played(self):
        matches = [
            Match(self.players[0], self.players[1]),
            Match(self.players[2], self.players[3]),
            Match(self.players[4], self.players[5]),
            Match(self.players[6], self.players[7]),
        ]
        self.matchmaker.matches.append(matches)
        
        # these should all be round 1
        TURN = 1
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[0], self.players[1]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[2], self.players[3]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[4], self.players[5]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[6], self.players[7]), 1
        )
        # pick some examples and verify there are no matches yet
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[0], self.players[2]), 0
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[0], self.players[6]), 0
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[3], self.players[7]), 0
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[4], self.players[1]), 0
        )

        # add a new turn
        TURN = 2
        new_matches = [
            Match(self.players[0], self.players[4]),
            Match(self.players[1], self.players[5]),
            Match(self.players[2], self.players[6]),
            Match(self.players[3], self.players[7]),
        ]
        self.matchmaker.matches.append(new_matches)
        # these were just played
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[0], self.players[4]), 2
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[1], self.players[5]), 2
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[2], self.players[6]), 2
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[3], self.players[7]), 2
        )

        # ensure that we still have old matches correct
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[0], self.players[1]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[2], self.players[3]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[4], self.players[5]), 1
        )
        self.assertEqual(
            self.matchmaker.previous_match_between_players(self.players[6], self.players[7]), 1
        )


class TestMatchmaker(unittest.TestCase):
    """
    Create some players and organize some matches.

    The expected results are determined from running the matchmaker once and setting
    a fixed seed for the random number generator.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        humans = [
            Player('Ashe Ketchum', type_=EntityType.HUMAN),
            Player('Red Dawn', type_=EntityType.HUMAN),
            Player('Blue Steel', type_=EntityType.HUMAN),
            Player('Yellow Fever', type_=EntityType.HUMAN),
            Player('Gold Digger', type_=EntityType.HUMAN),
            Player('Crystal Meth', type_=EntityType.HUMAN),
        ]
        computers = [
            Player('Skynet'),
            Player('HAL')
        ]

        cls.humans = humans
        cls.computers = computers
        cls.players = humans + computers

        for player in cls.players:
            player.is_alive = True

        cls.state = mock.MagicMock()
        cls.state.players = cls.players

    def test_organize_round(self):
        """
        Organize a round. Fix the seed and check the result matches expected.
        """
        random.seed(0)
        matchmaker = Matchmaker(self.state)
        round = matchmaker.organize_round()
        # TODO: actually add a results check here but right now tbh I don't really care

    def test_organize_round_with_dead_players(self):
        """
        Verify that dead players aren't matchmade
        """
        matchmaker = Matchmaker(self.state)
        try:
            self.humans[0].is_alive = False
            round = matchmaker.organize_round()
            # TODO: do more than a check on whether we can organize
        finally:
            # always set the player back to alive after this test
            self.humans[0].is_alive = True


class TestCreepRoundManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        humans = [
            Player('Ashe Ketchum', type_=EntityType.HUMAN),
            Player('Red Dawn', type_=EntityType.HUMAN),
            Player('Blue Steel', type_=EntityType.HUMAN),
            Player('Yellow Fever', type_=EntityType.HUMAN),
            Player('Gold Digger', type_=EntityType.HUMAN),
            Player('Crystal Meth', type_=EntityType.HUMAN),
        ]
        computers = [
            Player('Skynet'),
            Player('HAL')
        ]

        cls.humans = humans
        cls.computers = computers
        cls.players = humans + computers

        for player in cls.players:
            player.is_alive = True

        cls.state = mock.MagicMock()
        cls.state.players = cls.players

    def setUp(self):
        self.creep_round_manager = CreepRoundManager(self.state)

    def test_organize_creep_round(self):
        """
        Organize a creep round. Make sure that all alive players get a creep round matchup
        """
        human_creep_round = self.creep_round_manager.organize_creep_round()
        for match in human_creep_round:
            if not match.is_creep_match:
                raise ValueError("Creep round has PvP matchups")


if __name__ == "__main__":
    unittest.main()
