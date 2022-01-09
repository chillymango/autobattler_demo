import functools
import sys
import threading
import time
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

from engine.player import EntityType
from engine.player import Player
from engine.state import GamePhase, GameState
from screens.debug_battle_window import Ui as DebugWindow
from screens.storage_window import Ui as StorageWindow


class Ui(QtWidgets.QMainWindow):

    DEBUG = True

    def __init__(self, state: GameState = None):
        super(Ui, self).__init__()

        if state is None:
            self.player = Player("Albert Yang", type_=EntityType.HUMAN)
            self.state = GameState([self.player])
        else:
            self.player = self.state.current_player
            self.state = state

        uic.loadUi('qtassets/battlewindow.ui', self)

        if self.DEBUG:
            self.window = DebugWindow(self.state)

        # shop buttons
        self.update_shop_signal = QtCore.pyqtSignal()
        self.exploreWilds = self.findChild(QtWidgets.QPushButton, "exploreWilds")
        self.shopPokemon = [
            self.findChild(QtWidgets.QPushButton, "shopPokemon{}".format(idx))
            for idx in range(5)
        ]
        # initialize from current shop offerings
        for idx, shop_button in enumerate(self.shopPokemon):
            text = self.state.shop_manager.shop[self.player][idx]
            shop_button.setText(text)
            if not text:
                shop_button.setDisabled(True)
            else:
                shop_button.setDisabled(False)
            shop_button.clicked.connect(functools.partial(self.catch_pokemon_callback, idx))

        self.exploreWilds.clicked.connect(self.roll_shop_callback)

        # party buttons
        self.manageStorage = self.findChild(QtWidgets.QPushButton, "manageStorage")
        self.manageStorage.clicked.connect(self.open_storage_window)
        self.partyPokemon = [
            self.findChild(QtWidgets.QPushButton, "partyPokemon{}".format(idx))
            for idx in range(6)
        ]
        self.addParty = [
            self.findChild(QtWidgets.QPushButton, "addParty{}".format(idx))
            for idx in range(6)
        ]
        self.partyItems = [
            self.findChild(QtWidgets.QPushButton, "partyItems{}".format(idx))
            for idx in range(6)
        ]
        for idx, add_party in enumerate(self.addParty):
            add_party.clicked.connect(functools.partial(self.add_to_team_callback, idx))
        self.render_party()

        # team buttons
        self.teamMember = [
            self.findChild(QtWidgets.QPushButton, "teamMember{}".format(idx))
            for idx in range(3)
        ]
        self.removeTeamMember = [
            self.findChild(QtWidgets.QPushButton, "removeTeamMember{}".format(idx))
            for idx in range(3)
        ]
        self.shiftTeamMemberUp = [
            self.findChild(QtWidgets.QPushButton, "shiftTeam{}Up".format(idx))
            for idx in range(3)
        ]
        self.shiftTeamMemberDown = [
            self.findChild(QtWidgets.QPushButton, "shiftTeam{}Down".format(idx))
            for idx in range(3)
        ]
        for idx in range(3):
            self.removeTeamMember[idx].clicked.connect(
                functools.partial(self.remove_team_member_callback, idx)
            )
            self.shiftTeamMemberUp[idx].clicked.connect(
                functools.partial(self.shift_up_callback, idx)
            )
            self.shiftTeamMemberDown[idx].clicked.connect(
                functools.partial(self.shift_down_callback, idx)
            )
        self.render_team()

        # opposing party interface
        self.opponentName = self.findChild(QtWidgets.QLabel, "opponentName")
        self.opposingPokemon = [
            self.findChild(QtWidgets.QPushButton, "opposingPokemon{}".format(idx))
            for idx in range(6)
        ]

        # player stats
        self.pokeBallCount = self.findChild(QtWidgets.QLineEdit, "pokeBallCount")
        self.energyCount = self.findChild(QtWidgets.QLineEdit, "energyCount")
        self.hitPoints = self.findChild(QtWidgets.QLineEdit, "hitPoints")

        # time to next stage
        self.timeToNextStage = self.findChild(QtWidgets.QProgressBar, "timeToNextStage")

        # TODO: do something smarter than this
        for callback in [
            self.render_party,
            self.render_shop,
            self.render_team,
            self.render_player_stats,
            self.render_opponent_party,
            self.render_time_to_next_stage,
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def render_time_to_next_stage(self):
        state: GameState = self.state
        if state.phase not in [
            GamePhase.TURN_DECLARE_TEAM,
            GamePhase.TURN_PREPARE_TEAM,
            GamePhase.TURN_COMPLETE,
        ]:
            text = ""
            self.timeToNextStage.setFormat(text)
            self.timeToNextStage.setMaximum(1)
            self.timeToNextStage.setValue(0)
            return

        if state.phase == GamePhase.TURN_DECLARE_TEAM:
            text = "Party Declaration"
        elif state.phase == GamePhase.TURN_PREPARE_TEAM:
            text = "Team Preparation"
        elif state.phase == GamePhase.TURN_COMPLETE:
            text = "Match Complete"        

        stage_duration_ms = int(1E3 * state.stage_duration)
        stage_time_ms = int(1E3 * state.time_to_next_stage)
        self.timeToNextStage.setFormat(text)
        self.timeToNextStage.setMaximum(stage_duration_ms)
        self.timeToNextStage.setValue(stage_time_ms)

    def open_storage_window(self):
        self.storage_window = StorageWindow(game_state=self.state)

    def render_player_stats(self):
        player = self.state.current_player
        self.pokeBallCount.setText(str(player.balls))
        self.energyCount.setText(str(player.energy))
        self.hitPoints.setText(str(player.hitpoints))

    def render_opponent_party(self):
        player = self.state.current_player
        if self.state.matchmaker.current_matches is not None:
            opponent = self.state.matchmaker.get_player_opponent_in_round(
                player, self.state.matchmaker.current_matches
            )
            if opponent is not None:
                self.opponentName.setText("{} ({})".format(opponent.name, opponent.hitpoints))
                for idx in range(6):
                    if opponent.party[idx] is not None:
                        self.opposingPokemon[idx].setText(opponent.party[idx].name)
                    else:
                        self.opposingPokemon[idx].setText("Opposing Pokemon {}".format(idx + 1))
                return

        self.opponentName.setText("No Match Scheduled")
        for idx in range(6):
            self.opposingPokemon[idx].setText("Opposing Pokemon {}".format(idx + 1))
            self.opposingPokemon[idx].setDisabled(True)

    def render_party(self):
        player = self.state.current_player
        party = player.party
        for idx, party_member in enumerate(party):
            party_button = self.partyPokemon[idx]
            release_button = self.addParty[idx]
            item_button = self.partyItems[idx]

            if party_member is None:
                party_button.setDisabled(True)
                party_button.setText('Team Pokemon {}'.format(idx + 1))
                release_button.setDisabled(True)
                item_button.setDisabled(True)
            else:
                party_button.setText(party_member.name)
                party_button.setDisabled(False)
                release_button.setDisabled(False)
                item_button.setDisabled(False)

    def render_team(self):
        player = self.state.current_player
        team = player.team
        arr = [x for x in team]
        if len(arr) < 3:
            arr.extend([None] * (3 - len(arr)))
        for idx, team_member in enumerate(arr):
            team_member_button = self.teamMember[idx]
            remove_team_member = self.removeTeamMember[idx]
            shift_team_up = self.shiftTeamMemberUp[idx]
            shift_team_down = self.shiftTeamMemberDown[idx]
            if team_member is None:
                team_member_button.setDisabled(True)
                team_member_button.setText("Team Member {}".format(idx + 1))
                remove_team_member.setDisabled(True)
                shift_team_up.setDisabled(True)
                shift_team_down.setDisabled(True)
            else:
                team_member_button.setDisabled(False)
                team_member_button.setText(str(team_member))
                remove_team_member.setDisabled(False)
                shift_team_up.setDisabled(False)
                shift_team_down.setDisabled(False)

    def render_shop(self):
        for idx, shop_button in enumerate(self.shopPokemon):
            text = self.state.shop_manager.shop[self.player][idx]
            shop_button.setText(text)
            if not text:
                shop_button.setDisabled(True)
            else:
                shop_button.setDisabled(False)

    def roll_shop_callback(self):
        print("Rolling shop")
        self.state.shop_manager.roll(self.player)
        self.render_shop()

    def catch_pokemon_callback(self, idx):
        print("Acquiring Pokemon at index {}".format(idx))
        self.state.shop_manager.catch(self.player, idx)
        self.render_shop()
        self.render_party()

    def add_to_team_callback(self, idx):
        print("Adding pokemon at index {} to team".format(idx))
        self.state.current_player.add_party_to_team(idx)

    def remove_team_member_callback(self, idx):
        print("Removing team member at idx {} from team".format(idx))
        self.state.current_player.remove_from_team(idx)

    def shift_up_callback(self, idx):
        print("Shifting team member at {} up".format(idx))
        if idx == 0:
            return
        self.state.current_player.team[idx], self.state.current_player.team[idx - 1] =\
            self.state.current_player.team[idx - 1], self.state.current_player.team[idx]

    def shift_down_callback(self, idx):
        print("Shifting team member at {} down".format(idx))
        if idx == 2:
            return
        self.state.current_player.team[idx], self.state.current_player.team[idx + 1] =\
            self.state.current_player.team[idx + 1], self.state.current_player.team[idx]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
