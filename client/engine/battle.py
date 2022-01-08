"""
Battle Manager
"""
import re
from engine.base import Component

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


class BattleCard:

    def __init__(
        self,
        name,
        move_f,
        move_ch,
        move_tm,
        level,
        a_iv,
        d_iv,
        hp_iv,
        tm_flag,
        shiny,
        attack_stg,
        def_stg
    ):
        """
        Battle Card representation for a Pokemon.

        This should be generated by a Pokemon entry from a player roster and should be fed
        to the battle simulator.
        """
        self.name = name
        self.move_f = move_f
        self.move_ch = move_ch
        self.move_tm = move_tm
        self.level = level
        self.a_iv = a_iv
        self.d_iv = d_iv
        self.hp_iv = hp_iv
        self.tm_flag = tm_flag
        self.attack_stg = attack_stg
        self.def_stg = def_stg
        self.shiny = shiny

    @classmethod
    def from_string(cls, string):
        """
        Parse from a comma-delimited string
        """
        l = string.split(',')
        return BattleCard(
            name = l[0],
            move_f = l[1],
            move_ch = l[2],
            move_tm = l[3],
            level = l[4],
            a_iv = l[5], 
            d_iv = l[6], 
            hp_iv = l[7],
            tm_flag = 0,
            attack_stg = 0,
            def_stg = 0,
            shiny = 0
        )

    def to_string(self):
        """
        Return a PvPoke string representation of the Pokemon
        """
        return ",".join(str(x) for x in [
            self.name,
            self.move_f,
            self.move_ch,
            self.move_tm,
            self.level,
            self.a_iv,
            self.d_iv,
            self.hp_iv,
        ])


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.
    """

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


if __name__ == "__main__":
    from engine.player import Player, EntityType
    from engine.state import GameState
    player = Player('Albert Yang', type_=EntityType.HUMAN)
    state = GameState([player])
    battle_manager = BattleManager(state)

    team1 = battle_manager.create_team_battle_cards(['charizard', 'mewtwo', 'dragonite'])
    team2 = battle_manager.create_team_battle_cards(['magikarp', 'butterfree', 'blastoise'])

    result = battle_manager.battle(team1, team2)
    if sum(result) > 4:
        print('team 1 wins')
    else:
        print('team 2 wins')
