"""
NOTE: UNDEPRECATED!!!!
Battle Manager
"""
import copy
import typing as T

from engine.base import Component
from engine.batterulogico import battle
from engine.models.player import Player

if T.TYPE_CHECKING:
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
        player_manager: "PlayerManager" = self.env.player_manager
        # populate teams for both players in case they did not do so themselves
        player1.party_config.populate_team_from_party()
        player2.party_config.populate_team_from_party()

        p1_team = player_manager.player_team(player1)
        p2_team = player_manager.player_team(player2)
        p1_cards = [copy.deepcopy(poke.battle_card) for poke in p1_team]
        p2_cards = [copy.deepcopy(poke.battle_card) for poke in p2_team]

        return battle(p1_cards, p2_cards)

    def turn_execute(self):
        """
        For all matches, run battles.
        """
        matches = self.state.current_matches
        for match in matches:
            p1 = self.state.get_player_by_id(match.player1)
            p2 = self.state.get_player_by_id(match.player2)
            res = self.battle(p1, p2)
            if res['winner'] == 'team1':
                self.log(msg=f"{p1} beats {p2}", recipient=[p1, p2])
                losing_player = (p2,)
            elif res['winner'] == 'team2':
                self.log(msg=f"{p2} beats {p1}", recipient=[p1, p2])
                losing_player = (p1,)
            else:
                self.log(msg=f"{p1} and {p2} tie", recipient=[p1, p2])
                losing_player = (p1, p2)

            if losing_player is not None:
                for player in losing_player:
                    if self.state.stage.stage <= 4:
                        player.hitpoints -= 2
                    elif self.state.stage.stage <= 7:
                        player.hitpoints -= 4
                    else:
                        player.hitpoints -= 6
