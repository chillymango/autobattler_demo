"""
Screen should provide debug functions for the battle window
"""
import threading
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from engine.battle_seq import BattleManager
from engine.logger import Logger
from engine.match import Matchmaker
from engine.sprites import SpriteManager
from engine.state import GamePhase
from engine.state import Environment
from utils.error_window import error_window


class Ui(QtWidgets.QDialog):

    def __init__(self, env=None):
        super(Ui, self).__init__()
        self.env = env
        logger: Logger = self.env.logger
        self.log = logger.log
        self.runner: threading.Thread = None
        self.stop_game = threading.Event()
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

        self.addEnergy = self.findChild(QtWidgets.QPushButton, "addEnergy")
        self.addEnergy.clicked.connect(self.add_energy_callback)

        self.gamePhase = self.findChild(QtWidgets.QLineEdit, "gamePhase")

        self.startGame = self.findChild(QtWidgets.QPushButton, "startGame")
        self.startGame.clicked.connect(self.start_game_callback)

        self.devConsole = self.findChild(QtWidgets.QPushButton, "devConsole")
        self.devConsole.clicked.connect(self.dev_console_callback)

        self.disableSprites = self.findChild(QtWidgets.QPushButton, "disableSprites")
        self.disableSprites.clicked.connect(self.disable_sprites)

        self.enableSprites = self.findChild(QtWidgets.QPushButton, "enableSprites")
        self.enableSprites.clicked.connect(self.enable_sprites)

        self.disableLogTimestamps = self.findChild(QtWidgets.QPushButton, "disableLogTimestamps")
        self.disableLogTimestamps.clicked.connect(self.disable_log_timestamps)

        self.enableLogTimestamps = self.findChild(QtWidgets.QPushButton, "enableLogTimestamps")
        self.enableLogTimestamps.clicked.connect(self.enable_log_timestamps)

        for callback in [
            self.update_game_phase
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def disable_log_timestamps(self):
        logger: Logger = self.env.logger
        logger.TIMESTAMPS = False

    def enable_log_timestamps(self):
        logger: Logger = self.env.logger
        logger.TIMESTAMPS = True

    def disable_sprites(self):
        sprite_manager: SpriteManager = self.env.sprite_manager
        sprite_manager.DISABLED = True

    def enable_sprites(self):
        sprite_manager: SpriteManager = self.env.sprite_manager
        sprite_manager.DISABLED = False

    def add_energy_callback(self):
        if self.env is None:
            error_window("No active game")
            return
        
        print("Adding 100 energy")
        self.env.current_player.energy += 100

    def dev_console_callback(self):
        env: Environment = self.env
        import IPython; IPython.embed()

    def start_game_callback(self):
        """
        Initiate the game.
        """
        env: Environment = self.env
        env.start_game()

        self.stop_game.clear()

        def run_loop():
            while not self.stop_game.is_set():
                env.step_loop()

        self.runner = threading.Thread(target=run_loop)
        self.runner.daemon = True
        self.runner.start()

    def update_game_phase(self):
        """
        Print the current game state phase
        """
        env: Environment = self.env
        self.gamePhase.setText(env.phase.name)

    def make_new_matches_callback(self):
        if self.env is None:
            error_window("No active game")
            return

        print("Making new matches")
        round = self.env.matchmaker.organize_round()
        self.env.matchmaker.matches.append(round)

    def run_battle_callback(self):
        if self.env is None:
            error_window("No active game")
            return

        print("Running battle callback")
        player = self.env.current_player
        battle_manager: BattleManager = self.env.battle_manager
        matchmaker: Matchmaker = self.env.matchmaker
        opponent = matchmaker.get_player_opponent_in_round(player, matchmaker.current_matches)
        result = battle_manager.player_battle(player, opponent)
        if (result == 1):
            print('player victory')
        else:
            print('creep victory')

    def step_turn_forward_callback(self):
        if self.env is None:
            error_window("No active game")
            return

        print("Stepping turn forward one.")
        self.env.turn.advance()
        print("Turn number is now {}".format(self.env.turn.number))

    def step_turn_backward_callback(self):
        if self.env is None:
            error_window("No active game")
            return

        print("Stepping turn backward one.")
        self.env.turn.retract()
        print("Turn number is now {}".format(self.env.turn.number))

    def add_pokeballs_callback(self):
        if self.env is None:
            error_window("No active game")
            return
        
        print("Adding 100 pokeballs")
        self.env.current_player.balls += 100
