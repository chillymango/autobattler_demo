"""
Screen should provide debug functions for the battle window
"""
from os import error
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from engine.battle import BattleManager
from engine.match import Matchmaker

from utils.error_window import error_window


class Ui(QtWidgets.QDialog):

    def __init__(self, game_state=None):
        super(Ui, self).__init__()
        self.game_state = game_state
        uic.loadUi('qtassets/debug_battlewindow.ui', self)

        #self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        #self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        self.makeNewMatches = self.findChild(QtWidgets.QPushButton, "makeNewMatches")
        self.makeNewMatches.clicked.connect(self.make_new_matches_callback)
        self.runBattle = self.findChild(QtWidgets.QPushButton, "runBattle")
        self.runBattle.clicked.connect(self.run_battle_callback)
        self.stepTurnForward = self.findChild(QtWidgets.QPushButton, "stepTurnForward")
        self.stepTurnForward.clicked.connect(self.step_turn_forward_callback)
        self.stepTurnBackward = self.findChild(QtWidgets.QPushButton, "stepTurnBackward")
        self.stepTurnBackward.clicked.connect(self.step_turn_backward_callback)

        self.addPokeBalls = self.findChild(QtWidgets.QPushButton, "addPokeBalls")
        self.addPokeBalls.clicked.connect(self.add_pokeballs_callback)

        self.show()

    def make_new_matches_callback(self):
        if self.game_state is None:
            error_window("No active game")
            return

        print("Making new matches")
        round = self.game_state.matchmaker.organize_round()
        self.game_state.matchmaker.matches.append(round)

    def run_battle_callback(self):
        if self.game_state is None:
            error_window("No active game")
            return

        print("Running battle callback")
        player = self.game_state.current_player
        battle_manager: BattleManager = self.game_state.battle_manager
        matchmaker: Matchmaker = self.game_state.matchmaker
        opponent = matchmaker.get_player_opponent_in_round(player, matchmaker.current_matches)
        result = battle_manager.player_battle(player, opponent)
        if sum(result) > 4:
            print('player victory')
        else:
            print('creep victory')

    def step_turn_forward_callback(self):
        if self.game_state is None:
            error_window("No active game")
            return

        print("Stepping turn forward one.")
        self.game_state.turn.advance()
        print("Turn number is now {}".format(self.game_state.turn.number))

    def step_turn_backward_callback(self):
        if self.game_state is None:
            error_window("No active game")
            return

        print("Stepping turn backward one.")
        self.game_state.turn.retract()
        print("Turn number is now {}".format(self.game_state.turn.number))

    def add_pokeballs_callback(self):
        if self.game_state is None:
            error_window("No active game")
            return
        
        print("Adding 100 pokeballs")
        self.game_state.current_player.balls += 100
