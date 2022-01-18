"""
Screen should provide debug functions for the battle window
"""
import asyncio
import logging
import threading
import typing as T
from qasync import asyncSlot
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from engine.battle_seq import BattleManager
from engine.logger import Logger
from engine.match import Matchmaker
from engine.sprites import SpriteManager

from client.screens.base import GameWindow
from utils.error_window import error_window
from server.api.base import PlayerContextRequest
from utils.client import AsynchronousServerClient
from utils.client import GameServerClient
from utils.context import GameContext

if T.TYPE_CHECKING:
    from engine.env import Environment


class Ui(QtWidgets.QDialog, GameWindow):

    def __init__(self, parent, env: "Environment"):
        super(Ui, self).__init__()
        self.parent = parent
        self.env = env
        logger: Logger = self.env.logger
        self.log = logger.log
        self.runner: threading.Thread = None
        self.stop_game = threading.Event()

        # TODO: probably want to share client with parent window
        loop = asyncio.get_event_loop()
        self.client = AsynchronousServerClient(loop=loop)            
        
        uic.loadUi('client/qtassets/debug_battlewindow.ui', self)

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
            #self.update_game_phase
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    @property
    def context(self):
        """
        TODO: probably want to implement something cleaner here
        """
        return self.parent.context

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

    def dev_console_callback(self):
        env: Environment = self.env
        import IPython; IPython.embed()

    @asyncSlot()
    async def start_game_callback(self):
        """
        Initiate the game.
        """
        #env: Environment = self.env
        #env.start_game()

        #self.stop_game.clear()

#        def run_loop():
#            while not self.stop_game.is_set():
#                env.step_loop()
#
#        self.runner = threading.Thread(target=run_loop)
#        self.runner.daemon = True
#        self.runner.start()

    def update_game_phase(self):
        """
        Print the current game state phase
        """
        env: Environment = self.env
        self.gamePhase.setText(env.state.phase.name)

    @asyncSlot()
    async def make_new_matches_callback(self):
        print("Making new matches")
        try:
            await self.client.make_new_matches(self.env.id)
        except Exception as exc:
            print(f'Exception encountered: {exc}')

    @asyncSlot()
    async def run_battle_callback(self):
        print("Running battle callback")
        # TODO: implement
        print("This button doesn't work!!!")

    @asyncSlot()
    async def step_turn_forward_callback(self):
        print("Stepping turn forward one.")
        try:
            await self.client.advance_turn(self.env.id)
        except Exception as exc:
            print(f'Exception encountered: {exc}')
            raise        

    @asyncSlot()
    async def step_turn_backward_callback(self):
        print("Stepping turn back one.")
        try:
            await self.client.retract_turn(self.env.id)
        except Exception as exc:
            print(f'Exception encountered: {exc}')
            raise

    @asyncSlot()
    async def add_pokeballs_callback(self):
        request = PlayerContextRequest(player=self.context.player, game_id=str(self.env.id))
        try:
            await self.client.add_pokeballs(request)
        except Exception as exc:
            print(f'Exception encountered: {exc}')
            raise
        print('Finished adding 100 pokeballs')

    @asyncSlot()
    async def add_energy_callback(self):
        if self.env is None:
            error_window("No active game")
            return
        print("Adding 100 energy")
        request = PlayerContextRequest(player=self.context.player, game_id=str(self.env.id))
        await self.client.add_energy(request)
        print('Finished adding 100 energy')

    def closeEvent(self, *args, **kwargs):
        self.parent.debug_window = None
        super().closeEvent(*args, **kwargs)
