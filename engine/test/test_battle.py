"""
Run some simulated battles

What this module IS: unit tests for the battle component
What this module IS NOT: unit tests for the battle logic
"""
import unittest
from engine.battle import BattleManager

from engine.env import Environment
from engine.models.player import Player
from engine.player import PlayerManager


class TestBattleComponent(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='yare yare')
        self.env.add_player(self.p1)
        self.env.initialize()

    def test_battle_shit(self):
        for component in self.env.components:
            component.turn_setup()

        # populate a Pokemon party for the player
        pm: PlayerManager = self.env.player_manager
        pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        pm.create_and_give_pokemon_to_player(self.p1, 'bulbasaur')
        pm.create_and_give_pokemon_to_player(self.p1, 'charmander')
        pm.create_and_give_pokemon_to_player(self.p1, 'squirtle')
        # intentionally do not configure teams and check the auto-pop logic

        battle: BattleManager = self.env.battle
        res = battle.battle(self.p1, self.env.state.creeps[0])
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
