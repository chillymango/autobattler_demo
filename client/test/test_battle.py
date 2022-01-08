import mock
import unittest

from engine.battle import BattleManager
from engine.player import EntityType
from engine.player import Player
from engine.pokemon import BattleCard
from engine.pokemon import Pokemon


class TestBattleManager(unittest.TestCase):
    """
    Test Battle Manager functionality
    """

    @classmethod
    def setUpClass(cls):
        cls.state = mock.MagicMock()
        cls.state.players = [Player('Albert Yang', type_=EntityType.HUMAN)]

    def setUp(self):
        self.battle_manager = BattleManager(self.state)

    def test_run_3v3_battle(self):
        team1_pokemon = [
            Pokemon(
                'victreebel',
                BattleCard.from_string('victreebel,RAZOR_LEAF,ACID_SPRAY,none,17,0,0,0')
            ),
            Pokemon(
                'lickitung',
                BattleCard.from_string('lickitung,LICK,BODY_SLAM,none,23,0,0,0')
            ),
            Pokemon(
                'raichu',
                BattleCard.from_string('raichu,SLAM,THUNDER,none,5,0,0,0')
            ),
        ]
        team2_pokemon = [
            Pokemon(
                'nidoqueen',
                BattleCard.from_string('nidoqueen,BITE,STONE_EDGE,none,13,0,0,0')
            ),
            Pokemon(
                'kangaskhan',
                BattleCard.from_string('kangaskhan,LOW_KICK,OUTRAGE,none,12,0,0,0')
            ),
            Pokemon(
                'cloyster',
                BattleCard.from_string('cloyster,FROST_BREATH,HYDRO_PUMP,none,17,0,0,0')
            ),
        ]
        self.battle_manager.battle(
            [x.battle_card for x in team1_pokemon],
            [x.battle_card for x in team2_pokemon],
        )


if __name__ == "__main__":
    unittest.main()
