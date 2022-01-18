"""
NOTE: !!!!!DEPRECATED!!!!!
SEE: battle_seq.py
Battle Manager
"""
import re
from engine.base import Component
from engine.match import Matchmaker
from engine.pokemon import BattleCard

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support.ui import Select
import random
import pandas as pd


def true_hit(result):
    a = random.randint(0,1000)
    b = random.randint(0,1000)
    if .5*(a+b) < int(result):
        return 1
    else:
        return 0


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.

    TODO: use protobuf jeeeez what a slog
    """

    REPORT_DIALOG = True

    def initialize(self):
        """
        Load movesets from data file
        """
        # start selenium stuff
        self.driver = webdriver.Firefox()
        self.driver.get('http://localhost/pvpoke/src/battle/matrix')
        self.battletype = Select(self.driver.find_element_by_class_name('league-select'))
        self.battletype.select_by_visible_text('Master League (Level 50)')

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

    def battle(self, team1_cards, team2_cards):
        # reduce cards to strings first
        team1 = [x.to_string() for x in team1_cards]
        team2 = [x.to_string() for x in team2_cards]

        self.driver.find_element(value="(//button[contains(@class, 'export-btn')])[1]", by=By.XPATH).click()
        self.driver.find_element(value="/html/body/div[2]/div/div[3]/div/textarea", by=By.XPATH).send_keys("\n".join(team1))
        self.driver.find_element(value="/html/body/div[2]/div/div[3]/div/div[2]/div", by=By.XPATH).click()

        self.driver.find_element(value="(//button[contains(@class, 'export-btn')])[2]", by=By.XPATH).click()
        self.driver.find_element(value="/html/body/div[2]/div/div[3]/div/textarea", by=By.XPATH).send_keys("\n".join(team2))
        self.driver.find_element(value="/html/body/div[2]/div/div[3]/div/div[2]/div", by=By.XPATH).click()

        self.driver.find_element(value="/html/body/div/div/div[4]/button[1]", by=By.XPATH).click()

        leadVlead = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[1]/td[1]/a", by=By.XPATH).text
        leadVmid = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[1]/td[2]/a", by=By.XPATH).text
        leadVrear = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[1]/td[3]/a", by=By.XPATH).text
        midVlead = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[2]/td[1]/a", by=By.XPATH).text
        midVmid = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[2]/td[2]/a", by=By.XPATH).text
        midVrear = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[2]/td[3]/a", by=By.XPATH).text
        rearVlead = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[3]/td[1]/a", by=By.XPATH).text
        rearVmid = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[3]/td[2]/a", by=By.XPATH).text
        rearVrear = self.driver.find_element(value="/html/body/div/div/div[4]/div[7]/div/div[2]/table/tbody/tr[3]/td[3]/a", by=By.XPATH).text
        
        result = [true_hit(leadVlead),true_hit(leadVmid),true_hit(leadVrear),true_hit(midVlead),true_hit(midVmid), true_hit(midVrear),true_hit(rearVlead),true_hit(rearVmid), true_hit(rearVrear)]
        
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
        matchmaker: Matchmaker = self.env.matchmaker
        if not matchmaker.current_matches:
            self._report("No matches to run")
            return

        for match in matchmaker.current_matches:
            result = self.player_battle(*match.players)
            # handle HP
            losing_player: Player = None
            if sum(result) > 5:
                winning_player = match.players[0]
                losing_player = match.players[1]
            else:
                winning_player = match.players[1]
                losing_player = match.players[0]
            msg = "Match won by {}".format(winning_player)
            # TODO: variable losses
            losing_player.hitpoints -= 2

            if match.has_player(self.env.current_player):
                self._report(msg)


if __name__ == "__main__":
    from engine.env import Environment
    from engine.player import Player, EntityType
    player = Player('Albert Yang', type_=EntityType.HUMAN)
    env = Environment([player])
    battle_manager = BattleManager(env)

    team1 = battle_manager.create_team_battle_cards(['charizard', 'mewtwo', 'dragonite'])
    team2 = battle_manager.create_team_battle_cards(['magikarp', 'butterfree', 'blastoise'])

    result = battle_manager.battle(team1, team2)
    if sum(result) > 4:
        print('team 1 wins')
    else:
        print('team 2 wins')
