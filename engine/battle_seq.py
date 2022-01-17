"""
Battle Manager
"""
import os
import typing as T
from engine.base import Component
from engine.logger import Logger
from engine.match import Matchmaker
from engine.logger import __ALL_PLAYERS__
from engine.models.player import EntityType
from engine.models.player import Player

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import random
import copy

if T.TYPE_CHECKING:
    from engine.models.state import State

# TODO: set this through options somehow
os.environ['MOZ_HEADLESS'] = '1'


class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.
    """

    REPORT_DIALOG = False

    def initialize(self):
        """
        Start selenium
        """
        # TODO: use this path
        if 'nt' in os.name:
            #options = webdriver.FirefoxOptions()
            options = Options()
            #options.binary_location = 
            self.driver = webdriver.Firefox(
                executable_path='client\\geckodriver.exe',
                options=options
            )
        else:
            self.driver = webdriver.Firefox()

        logger: Logger = self.env.logger

    def __del__(self):
        """
        Close the Selenium webdriver before exiting
        """
        if getattr(self, 'driver', None):
            # TODO: unhack
            try:
                self.driver.close()
            except:
                pass

    def get_battle_cards_for_player(self, player: Player):
        """
        Get a list of battle cards from a players team.

        If the team is incomplete, attempt to load party members into team.
        """
        battle_cards = [x.battle_card for x in player.team]
        if len(battle_cards) > 3:
            raise ValueError("Cannot submit a team of size > 3")
        if len(battle_cards) < 3:
            unassigned = [x for x in player.party if x not in player.team and x is not None]
            if player.type == EntityType.CREEP:
                # randomize for creep rounds
                unassigned = random.sample(unassigned, len(unassigned))
            for idx in range(min(3 - len(battle_cards), len(unassigned))):
                player.add_to_team(unassigned[idx])
                battle_cards.append(unassigned[idx].battle_card)
        return battle_cards

    def get_team_for_player(self, player: Player):
        """
        Get a list of Pokemon objects to initiate a fight with.

        If the team is incomplete, attempt to load party members into team.
        """
        team = [x for x in player.team]

        if len(player.team) > 3:
            raise ValueError("Cannot submit a team of size > 3")

        if len(team) < 3:
            unassigned = [x for x in player.party if x not in player.team and x is not None]
            if player.type == EntityType.CREEP:
                unassigned = random.sample(unassigned, len(unassigned))
            for idx in range(min(3 - len(team), len(unassigned))):
                player.add_to_team(unassigned[idx])
                team.append(unassigned[idx])

        return team

    def player_battle(self, player1, player2):
        """
        Orchestrate a battle between two players
        """
        self.log("Starting battle between {} and {}".format(player1, player2))
        team1 = self.get_team_for_player(player1)
        team2 = self.get_team_for_player(player2)
        self.log("{} sends out {}".format(player1, ", ".join([str(x) for x in team1])))
        self.log("{} sends out {}".format(player2, ", ".join([str(x) for x in team2])))
        return self.battle(team1, team2)

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

    def battle(self, team1, team2, player1=None, player2=None):
        players = [player1, player2]
        # team_cards is a dict of nickname to battle card
        team1_cards = [x.battle_card for x in team1]
        team2_cards = [x.battle_card for x in team2]
        team1_live = copy.deepcopy(team1_cards)
        team2_live = copy.deepcopy(team2_cards)

        team1_map = {str(x): copy.deepcopy(x.battle_card) for x in team1}
        team2_map = {str(x): copy.deepcopy(x.battle_card) for x in team2}

        # adjust level for fight RNG
        for i in team1_live:
            i.level = random.randint(i.level - 1, i.level + 1)
        for i in team2_live:
            i.level = random.randint(i.level - 1, i.level + 1)

        current_team1_pair = next(((x, y) for x, y in team1_map.items() if y.status == 1), None)
        current_team2_pair = next(((x, y) for x, y in team2_map.items() if y.status == 1), None)

        while (current_team1_pair != None) & (current_team2_pair != None):
            name1 = current_team1_pair[0]
            if player1:
                name1 = "{}'s {}".format(player1.name, name1)
            name2 = current_team2_pair[0]
            if player2:
                name2 = "{}'s {}".format(player2.name, name2)
            current_team1 = current_team1_pair[1]
            current_team2 = current_team2_pair[1]
            battle_result = self.oneVone(current_team1, current_team2)
            if battle_result[0] == 0:
                self.log("Simultaneous KO by " + name1 + " and " + name2, recipients=players)
                current_team1.status = 0
                current_team2.status = 0
            elif battle_result[0] == 1:
                self.log(name1 + " knocks out " + name2, recipients=players)
                current_team2.status = 0
                current_team1.health = battle_result[1]
                current_team1.energy = battle_result[2]
                current_team1.bonus_shield = battle_result[3] - 1
            elif battle_result[0] == 2:
                self.log(name2 +" knocks out " + name1, recipients=players)
                current_team1.status = 0
                current_team2.health = battle_result[1]
                current_team2.energy = battle_result[2]
                current_team2.bonus_shield = battle_result[3] - 1

            current_team1_pair = next(((x, y) for x, y in team1_map.items() if y.status == 1), None)
            current_team2_pair = next(((x, y) for x, y in team2_map.items() if y.status == 1), None)

        if (current_team1_pair == None) and (current_team2_pair == None):
            result = 0
        elif (current_team1_pair != None):
            result = 1
        elif (current_team2_pair != None):
            result = 2

        return result

    def turn_execute(self):
        """
        Run all matches and report results.

        Create a UI window for match results if there is one.

        Battle manager also calculates damage for players and will modify player health.
        """
        state: State = self.state
        matchmaker: Matchmaker = self.env.matchmaker
        if not state.current_matches:
            print("No matches to run")
            return

        print('Running matches')
        for match in self.state.current_matches:
            result = self.player_battle(*match.players)
            # handle HP
            losing_player: Player = None
            winning_player: Player = None
            if result == 1:
                winning_player = match.players[0]
                losing_player = match.players[1]
            elif result == 2:
                winning_player = match.players[1]
                losing_player = match.players[0]
            msg = "Match won by {}".format(winning_player)
            # TODO: variable losses, ties
            if losing_player is not None:
                losing_player.hitpoints -= 2

            # send messages to involved players
            for player in match.players:
                if player.is_creep:
                    continue
                self.log(msg, recipient=player)
