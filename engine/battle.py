"""
NOTE: UNDEPRECATED!!!!
Battle Manager
"""
import copy

from engine.base import Component
from engine.batterulogico import battle
from engine.models.player import Player
from engine.player import PlayerManager


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.

    Provides a game interface into the mystical batterulogico module.
    """

    REPORT_DIALOG = True
    ENV_PROXY = 'battle'

    def initialize(self):
        """
        Load movesets from data file
        """
        super().initialize()

    def battle(self, player1: Player, player2: Player):
        """
        Run a battle between two players using the batterulogico engine.
        """
        player_manager: PlayerManager = self.env.player_manager
        # populate teams for both players in case they did not do so themselves
        player1.party_config.populate_team_from_party()
        player2.party_config.populate_team_from_party()

        p1_team = player_manager.player_team(player1)
        p2_team = player_manager.player_team(player2)
        p1_cards = [copy.deepcopy(poke.battle_card) for poke in p1_team]
        p2_cards = [copy.deepcopy(poke.battle_card) for poke in p2_team]

        result = battle(p1_cards, p2_cards)

        return result
