import functools
import sys
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

from engine.player import EntityType
from engine.player import Player
from engine.shop import ShopManager
from engine.state import GamePhase, GameState
from screens.debug_battle_window import Ui as DebugWindow
from screens.storage_window import Ui as StorageWindow
from utils.buttons import set_border_color, set_border_color_and_image, set_button_image
from utils.buttons import clear_button_image
from utils.buttons import PokemonButton


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
            self.state.logger.DEBUG = True
            self.window = DebugWindow(self.state)
            self.window.battle_window = self

        # shop buttons
        self.update_shop_signal = QtCore.pyqtSignal()
        self.shopLocationLabel = self.findChild(QtWidgets.QLabel, "shopLocationLabel")
        self.exploreWilds = self.findChild(QtWidgets.QPushButton, "exploreWilds")
        self.shopPokemon = [
            self.findChild(QtWidgets.QPushButton, "shopPokemon{}".format(idx))
            for idx in range(5)
        ]
        self.shop_pokemon_buttons = [
            PokemonButton(qbutton, self.state, "") for idx, qbutton in enumerate(self.shopPokemon)
        ]
        # initialize from current shop offerings
        for idx, shop_button in enumerate(self.shop_pokemon_buttons):
            text = self.state.shop_manager.shop[self.player][idx]
            shop_button.render_shop_card(text)
            shop_button.button.clicked.connect(functools.partial(self.catch_pokemon_callback, idx))

        self.exploreWilds.clicked.connect(self.roll_shop_callback)

        # party buttons
        self.manageStorage = self.findChild(QtWidgets.QPushButton, "manageStorage")
        self.manageStorage.clicked.connect(self.open_storage_window)
        self.partyLabel = [
            self.findChild(QtWidgets.QLabel, "party{}Label".format(idx))
            for idx in range(6)
        ]
        self.partyPokemon = [
            self.findChild(QtWidgets.QPushButton, "partyPokemon{}".format(idx))
            for idx in range(6)
        ]
        self.party_pokemon_buttons = [
            PokemonButton(
                self.partyPokemon[idx],
                self.state,
                "Party Pokemon {}".format(idx + 1),
                label=self.partyLabel[idx]
            )
            for idx in range(len(self.partyPokemon))
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
        self.teamLabel = [
            self.findChild(QtWidgets.QLabel, "teamLabel{}".format(idx))
            for idx in range(3)
        ]
        self.team_member_button = [
            PokemonButton(
                self.teamMember[idx],
                self.state,
                default_text="Team {}".format(idx),
                label=self.teamLabel[idx]
            )
            for idx in range(len(self.teamMember))
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
        self.opposingLabel = [
            self.findChild(QtWidgets.QLabel, "opposingLabel{}".format(idx))
            for idx in range(6)
        ]
        self.opposing_pokemon_buttons = [
            PokemonButton(
                self.opposingPokemon[idx],
                self.state,
                "Opponent {}".format(idx + 1),
                label=self.opposingLabel[idx]
            )
            for idx in range(6)
        ]

        # player stats
        self.pokeBallCount = self.findChild(QtWidgets.QLineEdit, "pokeBallCount")
        self.energyCount = self.findChild(QtWidgets.QLineEdit, "energyCount")
        self.hitPoints = self.findChild(QtWidgets.QLineEdit, "hitPoints")

        # time to next stage
        self.timeToNextStage = self.findChild(QtWidgets.QProgressBar, "timeToNextStage")

        # update log messages
        self.logMessages = self.findChild(QtWidgets.QTextBrowser, "logMessages")
        self.logMessages.moveCursor(QtGui.QTextCursor.End)

        # TODO: do something smarter than this
        for callback in [
            self.render_party,
            self.render_shop,
            self.render_team,
            self.render_player_stats,
            self.render_opponent_party,
            self.render_time_to_next_stage,
            self.render_log_messages,
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def render_log_messages(self):
        """
        Update log messages

        TODO: this is going to change a lot in multiplayer but get something working for now
        """
        self.logMessages.setText(self.state.logger.content)
        #self.logMessages.moveCursor(QtGui.QTextCursor.End)

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
                    button = self.opposing_pokemon_buttons[idx]
                    pokemon = opponent.party[idx]
                    button.render_pokemon_card(pokemon)
                return

        self.opponentName.setText("No Match Scheduled")
        for idx in range(6):
            self.opposingPokemon[idx].setText("Opposing Pokemon {}".format(idx + 1))
            self.opposingPokemon[idx].setDisabled(True)

    def render_party(self):
        player = self.state.current_player
        party = player.party
        for idx, party_member in enumerate(party):
            party_button = self.party_pokemon_buttons[idx]
            release_button = self.addParty[idx]
            item_button = self.partyItems[idx]
            party_button.render_pokemon_card(party_member)

            if party_member is None:
                release_button.setDisabled(True)
                item_button.setDisabled(True)
            else:
                release_button.setDisabled(False)
                item_button.setDisabled(False)

    def render_team(self):
        player = self.state.current_player
        team = player.team
        arr = [x for x in team]
        if len(arr) < 3:
            arr.extend([None] * (3 - len(arr)))
        for idx, team_member in enumerate(arr):
            team_member_button = self.team_member_button[idx]
            remove_team_member = self.removeTeamMember[idx]
            shift_team_up = self.shiftTeamMemberUp[idx]
            shift_team_down = self.shiftTeamMemberDown[idx]
            team_member_button.render_pokemon_card(team_member)
            if team_member is None:
                remove_team_member.setDisabled(True)
                shift_team_up.setDisabled(True)
                shift_team_down.setDisabled(True)
            else:
                shift_team_up.setDisabled(False)
                shift_team_down.setDisabled(False)
                remove_team_member.setDisabled(False)

    def render_shop(self):
        shop_manager: ShopManager = self.state.shop_manager
        for idx, pokemon_name in enumerate(shop_manager.shop[self.player]):
            shop_button = self.shop_pokemon_buttons[idx]
            shop_button.render_shop_card(pokemon_name)

        # update shop location
        if self.state.turn.number:
            route = shop_manager.route[self.state.current_player]
            self.shopLocationLabel.setText(route.name)

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
