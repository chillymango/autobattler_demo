"""
Battle Manager
"""
from engine.base import Component
from engine.logger import Logger
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player

from selenium import webdriver
import random
import copy
import pandas as pd
import re

class BattleManager(Component):
    """
    Supports making battle callbacks to API server somewhere.

    Will make HP deductions as well.
    """

    REPORT_DIALOG = False

    def initialize(self):
        """
        Load movesets from data file
        """
        # start selenium stuff
        self.driver = webdriver.Firefox()

        logger: Logger = self.state.logger
        self.log = logger.log

    def __del__(self):
        """
        Close the Selenium webdriver before exiting
        """
        if getattr(self, 'driver', None):
            self.driver.close()

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

    def eat_berry(self, battler, team):
        """
        eat a berry
        """
        battler_position = battler.team_position
        team[battler_position].battle_card.berry = None

    def oneVone(self,battler1, battler2, team1, team2):
        if battler1.shiny == 1:
            DBUFF1 = 5
            ABUFF1 = 5

        else:
            DBUFF1 = 4
            ABUFF1 = 4
        if battler2.shiny == 1:
            DBUFF2 = 5
            ABUFF2 = 5
        else:
            DBUFF2 = 4
            ABUFF2 = 4
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

        choice_f_move = 'YAWN'
        choice_ch_move = 'FRUSTRATION'
        if battler1.choiced == 1:
            FMOVE1 = choice_f_move
            ABUFF1 += 1
            CHMOVE1 = battler1.move_ch
            TM1 = TM1
        elif battler1.choiced == 2:
            CHMOVE1 = choice_ch_move
            ABUFF1 += 1
            FMOVE1 = battler1.move_f
            TM1 = 0
        else:
            FMOVE1 = battler1.move_f
            CHMOVE1 = battler1.move_ch

        if battler2.choiced == 1:
            FMOVE2 = choice_f_move
            ABUFF2 += 1
            CHMOVE2 = battler2.move_ch
            TM1 = TM1
        elif battler2.choiced == 2:
            CHMOVE2 = choice_ch_move
            ABUFF2 += 1
            FMOVE2 = battler2.move_f
            TM1 = 0
        else:
            FMOVE2 = battler2.move_f
            CHMOVE2 = battler2.move_ch

        """
        Pre-battle berries: these trigger no matter what
        """
        if battler1.berry == 'Ganlon Berry':
            SHIELD1 += 1
            self.eat_berry(battler1, team1)
        if battler2.berry == 'Ganlon Berry':
            SHIELD2 += 1
            self.eat_berry(battler2, team2)

        if battler1.berry == 'Leppa Berry':
            battler1.energy += 20
            self.eat_berry(battler1, team1)
        if battler2.berry == 'Leppa Berry':
            battler2.energy += 20
            self.eat_berry(battler2, team2)

        if battler1.berry == 'Power Herb':
            battler1.energy += 40
            self.eat_berry(battler1, team1)
        if battler2.berry == 'Power Herb':
            battler2.energy += 40
            self.eat_berry(battler2, team2)


        url = f'http://localhost/pvpoke/src/battle/10000/{battler1.name}-{battler1.level}-{battler1.a_iv}-{battler1.d_iv}-{battler1.hp_iv}-{ABUFF1}-{DBUFF1}-1-0/{battler2.name}-{battler2.level}-{battler2.a_iv}-{battler2.d_iv}-{battler2.hp_iv}-{ABUFF2}-{DBUFF2}-1-0/{SHIELD1}{SHIELD2}/{FMOVE1}-{CHMOVE1}-{TM1}/{FMOVE2}-{CHMOVE2}-{TM2}/{battler1.health}-{battler2.health}/{battler1.energy}-{battler2.energy}/'
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

        """
        Battle Logging
        """
        battle_time = float(self.driver.find_element_by_xpath("/html/body/div/div/div[4]/div[2]/div[5]/div[1]/span[2]").text[:-1])

        battler_1_log = []

        parent_div = self.driver.find_element_by_xpath("//div[@class='timeline'][1]")
        count_of_divs = len(parent_div.find_elements_by_xpath("./div"))

        for i in range(1,(count_of_divs+1)):
            event = parent_div.find_element_by_xpath("./div["+str(i)+']/a')
            time_div = parent_div.find_element_by_xpath("./div["+str(i)+']')

            txt = time_div.get_attribute('style').split(' ')[1]
            time = re.search("\d+", txt)[0]

            battler_1_log.append(time + ', '+event.get_attribute('name') + ', ' + event.get_attribute('values'))


        battler_2_log = []

        parent_div = self.driver.find_element_by_xpath("//div[@class='timeline'][2]")
        count_of_divs = len(parent_div.find_elements_by_xpath("./div"))

        for i in range(1,(count_of_divs+1)):
            event = parent_div.find_element_by_xpath("./div["+str(i)+']/a')
            time_div = parent_div.find_element_by_xpath("./div["+str(i)+']')

            txt = time_div.get_attribute('style').split(' ')[1]
            time = re.search("\d+", txt)[0]

            battler_2_log.append(time + ', '+event.get_attribute('name') + ', ' + event.get_attribute('values'))

        battlelog_1_df = pd.DataFrame([sub.split(",") for sub in battler_1_log], columns=['Time', 'Event', 'Damage Dealt', 'Energy', 'Percent Damage Dealt'])
        battlelog_1_df['Event'] = battlelog_1_df['Event'].str.strip()
        battlelog_1_df.loc[battlelog_1_df['Event'] == 'Shield', "Damage Dealt"] = 0
        battlelog_1_df = battlelog_1_df[~battlelog_1_df.Event.isin(['Tap', 'Swipe'])].reset_index(drop = True)
        battlelog_1_df['Time'] = battle_time*(battlelog_1_df['Time'].astype('float')/100)

        battlelog_2_df = pd.DataFrame([sub.split(",") for sub in battler_2_log], columns=['Time', 'Event', 'Damage Dealt', 'Energy', 'Percent Damage Dealt'])
        battlelog_2_df['Event'] = battlelog_2_df['Event'].str.strip()
        battlelog_2_df.loc[battlelog_2_df['Event'] == 'Shield', "Damage Dealt"] = 0
        battlelog_2_df = battlelog_2_df[~battlelog_2_df.Event.isin(['Tap', 'Swipe'])].reset_index(drop = True)
        battlelog_2_df['Time'] = battle_time*(battlelog_2_df['Time'].astype('float')/100)


        """
        Post-battle berries: these trigger if you win
        """
        maxhp_p1 = self.driver.find_element_by_xpath("/html/body/div/div/div[3]/div[1]/div[2]/div[4]/div[1]/span[2]").text
        maxhp_p2 = self.driver.find_element_by_xpath("/html/body/div/div/div[3]/div[2]/div[2]/div[4]/div[1]/span[2]").text
        maxhp_l = [int(maxhp_p1), int(maxhp_p2)]
        battler_l = [battler1, battler2]
        winner_i = winner-1
        winner_p = battler_l[winner_i]

        team_l = [team1, team2]
        if winner_p.berry == 'Oran Berry':
            survivorhp += maxhp_l[winner_i]*0.1
            self.eat_berry(winner_p, team_l[winner_i])
        if winner_p.berry == 'Sitrus Berry':
            survivorhp += maxhp_l[winner_i]*0.3
            self.eat_berry(winner_p, team_l[winner_i])
        if winner_p.berry == 'Salac Berry':
            survivorenergy += 50
            self.eat_berry(winner_p, team_l[winner_i])
        if winner_p.berry == 'Apicot Berry':
            survivorshields += 1
            self.eat_berry(winner_p, team_l[winner_i])


        return([winner, survivorhp, survivorenergy,survivorshields])

    def battle(self, team1, team2, player1=None, player2=None):
        # team_cards is a dict of nickname to battle card
        team1_cards = [x.battle_card for x in team1]
        team2_cards = [x.battle_card for x in team2]
        for i in range(3):
            team1_cards[i].team_position = i
            team2_cards[i].team_position = i

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
            battle_result = self.oneVone(current_team1, current_team2, team1, team2)
            if battle_result[0] == 0:
                self.log("Simultaneous KO by " + name1 + " and " + name2)
                current_team1.status = 0
                current_team2.status = 0
                if current_team1.berry == 'Focus Band':
                    current_team1.status = 1
                    current_team1.health = 1
                    current_team1.energy = 100
                    current_team1.bonus_shield = -1
                    self.eat_berry(current_team1, team1)
                if current_team2.berry == 'Focus Band':
                    current_team2.status = 1
                    current_team2.health = 1
                    current_team2.energy = 100
                    current_team2.bonus_shield = -1
                    self.eat_berry(current_team2, team2)

            elif battle_result[0] == 1:
                self.log(name1 + " knocks out " + name2)
                current_team2.status = 0
                current_team1.health = battle_result[1]
                current_team1.energy = battle_result[2]
                current_team1.bonus_shield = battle_result[3] - 1
                if current_team2.berry == 'Focus Band':
                    current_team2.status = 1
                    current_team2.health = 1
                    current_team2.energy = 100
                    current_team2.bonus_shield = -1
                    self.eat_berry(current_team2, team2)

            elif battle_result[0] == 2:
                self.log(name2 +" knocks out " + name1)
                current_team1.status = 0
                current_team2.health = battle_result[1]
                current_team2.energy = battle_result[2]
                current_team2.bonus_shield = battle_result[3] - 1
                if current_team1.berry == 'Focus Band':
                    current_team1.status = 1
                    current_team1.health = 1
                    current_team1.energy = 100
                    current_team1.bonus_shield = -1

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
        matchmaker: Matchmaker = self.state.matchmaker
        if not matchmaker.current_matches:
            print("No matches to run")
            return

        for match in matchmaker.current_matches:
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

            if match.has_player(self.state.current_player):
                self.log(msg)


if __name__ == "__main__":
    from engine.player import Player, EntityType
    from engine.state import GameState
    player = Player('Albert Yang', type_=EntityType.HUMAN)
    state = GameState([player])
    battle_manager = BattleManager(state)
