"""
Battle Manager
"""
import re
from engine.base import Component
from engine.match import Matchmaker

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import By
import random
import pandas as pd
import copy


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.
    """

    REPORT_DIALOG = True

    def initialize(self):
        """
        Load movesets from data file
        """
        # start selenium stuff
        self.driver = webdriver.Firefox()
        #self.driver.get('http://localhost/pvpoke/src/battle/matrix')

    def __del__(self):
        """
        Close the Selenium webdriver before exiting
        """
        if getattr(self, 'driver', None):
            self.driver.close()

    def player_battle(self, player1, player2):
        """
        Orchestrate a battle between two players
        """
        team1_battle_cards = [x.battle_card for x in player1.team]
        team2_battle_cards = [x.battle_card for x in player2.team]
        return self.battle(team1_battle_cards, team2_battle_cards)

    def oneVone(self,battler1, battler2):
        if battler1.shiny == 1:
            BUFF1 = 5
        else:
            BUFF1 = 4
        if battler2.shiny == 1:
            BUFF2 = 5
        else:
            BUFF2 = 4
        SHIELD1 = 1+battler1.bonus_shield
        SHIELD2 = 1+battler2.bonus_shield
        if battler1.tm_flag == 0:
            TM1 = 0
        else:
            TM1 = battler1.move_tm
        if battler2.tm_flag == 0:
            TM2 = 0
        else:
            TM2 = battler2.move_tm
        url = f'http://localhost/pvpoke/src/battle/10000/{battler1.name}-{battler1.level}-{battler1.a_iv}-{battler1.d_iv}-{battler1.hp_iv}-{BUFF1}-{BUFF1}-1-0/{battler2.name}-{battler2.level}-{battler2.a_iv}-{battler2.d_iv}-{battler2.hp_iv}-{BUFF2}-{BUFF2}-1-0/{SHIELD1}{SHIELD2}/{battler1.move_f}-{battler1.move_ch}-{TM1}/{battler2.move_f}-{battler2.move_ch}-{TM2}/{battler1.health}-{battler2.health}/{battler1.energy}-{battler2.energy}/'
        self.driver.get(url)
        result = self.driver.find_element_by_xpath("//div[@class='summary section white']").text.split()
        while len(result) == 0:
            result = self.driver.find_element_by_xpath("//div[@class='summary section white']").text.split()

        if result[0] == 'Simultaneous':
            winner = 0
            survivorhp = None
            survivorenergy = None
            survivorshields = None
        else:
            battle_score = int(self.driver.find_element_by_xpath("/html/body/div/div/div[4]/div[2]/div[5]/div[1]/span[3]").text)
            survivor = self.driver.find_element_by_xpath("/html/body/div/div/div[4]/div[3]/div[2]/p/span").text.split()
            survivorhp = int(survivor[0][1:])
            survivorenergy = int(survivor[2])
            survivorshields = int(survivor[4])

            if battle_score > 500:
                winner = 1
            else:
                winner = 2


        return([winner, survivorhp, survivorenergy,survivorshields])

    def battle(self, team1_cards, team2_cards):
        team1_live = copy.deepcopy(team1_cards)
        team2_live = copy.deepcopy(team2_cards)
        current_team1 = next((x for x in team1_live if x.status == 1), None)
        current_team2 = next((x for x in team2_live if x.status == 1), None)

        while (current_team1 != None ) & (current_team2 != None):
            battle_result = self.oneVone(current_team1,current_team2)
            if battle_result[0] == 0:
                print("Simultaneous KO by " +current_team1.name +" and " + current_team2.name)
                current_team1.status = 0
                current_team2.status = 0
            elif battle_result[0] == 1:
                print(current_team1.name +" knocks out " + current_team2.name)
                current_team2.status = 0
                current_team1.health = battle_result[1]
                current_team1.energy = battle_result[2]
                current_team1.bonus_shield = battle_result[3]-1

            elif battle_result[0] == 2:
                print(current_team2.name +" knocks out " + current_team1.name)
                current_team1.status = 0
                current_team2.health = battle_result[1]
                current_team2.energy = battle_result[2]
                current_team2.bonus_shield = battle_result[3]-1

            current_team1 = next((x for x in team1_live if x.status == 1), None)
            current_team2 = next((x for x in team2_live if x.status == 1), None)

        if (current_team1 == None) & (current_team2 == None):
            result = 0
        elif (current_team1 != None):
            result = 1
        elif (current_team2 != None):
            result = 2

        return result

    def _report(self, msg):
        """
        Battles are noteworthy enough that I'm currently setting them up to open a dialog box

        TODO: some sort of UI handler for this crap
        """
        if self.REPORT_DIALOG:
            from PyQt5 import QtWidgets
            window = QtWidgets.QMessageBox()
            window.setWindowTitle('Battle Result')
            window.setText(msg)
            window.exec_()
        else:
            print(msg)

    def turn_execute(self):
        """
        Run all matches and report results.

        Create a UI window for match results if there is one.

        Battle manager also calculates damage for players and will modify player health.
        """
        matchmaker: Matchmaker = self.state.matchmaker
        if not matchmaker.current_matches:
            self._report("No matches to run")
            return

        for match in matchmaker.current_matches:
            result = self.player_battle(*match.players)
            # handle HP
            losing_player: Player = None
            if result == 1:
                winning_player = match.players[0]
                losing_player = match.players[1]
            elif result == 2:
                winning_player = match.players[1]
                losing_player = match.players[0]
            msg = "Match won by {}".format(winning_player)
            # TODO: variable losses, ties
            losing_player.hitpoints -= 2

            if match.has_player(self.state.current_player):
                self._report(msg)


if __name__ == "__main__":
    from engine.player import Player, EntityType
    from engine.state import GameState
    player = Player('Albert Yang', type_=EntityType.HUMAN)
    state = GameState([player])
    battle_manager = BattleManager(state)

