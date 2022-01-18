"""
Landing Screen

Player will choose to create or join a game from here.
"""
import asyncio
import nest_asyncio
import sys
import traceback
import typing as T
import websockets

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot

from client.screens.battle_window import Ui as BattleWindow
from client.screens.lobby_window import Ui as LobbyWindow
from server.api.lobby import CreateGameResponse
from utils.error_window import error_window
from utils.server_config import ServerConfig

if T.TYPE_CHECKING:
    from utils.client import AsynchronousServerClient
    from server.api.user import User

nest_asyncio.apply()


class Ui(QtWidgets.QMainWindow):

    def __init__(self, client: "AsynchronousServerClient", server_config: ServerConfig):
        super(Ui, self).__init__()
        self.server_config = server_config
        self.client: "AsynchronousServerClient" = client
        uic.loadUi('client/qtassets/landingscreen.ui', self)

        # add hooks for UI buttons
        self.createMatch = self.findChild(QtWidgets.QPushButton, "createMatch")
        self.createMatch.clicked.connect(self.create_match_callback)
        self.joinMatch = self.findChild(QtWidgets.QPushButton, "joinMatch")
        self.joinMatch.clicked.connect(self.join_match_callback)
        self.configMenu = self.findChild(QtWidgets.QPushButton, "configMenu")
        self.configMenu.clicked.connect(self.config_callback)

        self._lobby_window = None
        self._battle_window = None

        self.show()

    def set_user(self, user: "User"):
        self.user = user

    @asyncSlot()
    async def create_match_callback(self):
        self.createMatch.setDisabled(True)
        self.createMatch.setText("Creating Match...")
        try:
            game_response: CreateGameResponse = await self.client.create_game(self.user)
            print(f'Created game with id {game_response.game_id}')
            # join the game and open the lobby window
            join_response = await self.client.join_game(game_response.game_id, self.user)
            if not join_response.success:
                raise Exception("Failed to join game")
            if self._lobby_window is not None:
                self._lobby_window.game_id = game_response.game_id
            else:
                self._lobby_window = LobbyWindow(
                    parent=self,
                    user=self.user,
                    client=self.client,
                    game_id=game_response.game_id
                )
            # start subscribing to state updates over pubsub
            self._lobby_window.start_pubsub_subscription()
            print(self.server_config.pubsub_path)
            self._lobby_window.pubsub_client.start_client(self.server_config.pubsub_path)
            # do not transfer windows until pubsub connection established
            await self._lobby_window.pubsub_client.wait_until_ready()
            self._lobby_window.show()
            self.hide()
        except Exception as exc:
            error_window(str(exc))
        finally:
            self.createMatch.setDisabled(False)
            self.createMatch.setText("Create Match")

    async def open_battle_window(self):
        # always instantiate a new window
        # TODO: garbage collect the old window...
        # try to get a game ID
        game_id = self._lobby_window.game_id

        # open a WebSocket
        try:
            ws_addr = self.server_config.websocket_path
            print(f'Opening WebSocket connection to {ws_addr}')
            ws = await websockets.connect(ws_addr)
        except Exception as exc:
            error_window(f'Unable to connect to the game: {repr(exc)}')
            raise

        try:
            print('Init Battle Window')
            self._battle_window = BattleWindow(user=self.user, client=self.client, game_id=game_id, websocket=ws)
            print('show Battle Window')
            self._battle_window.show()
            print('Subscribe States')
            self._battle_window.subscribe_pubsub_state()
            self._battle_window.subscribe_pubsub_messages()
            print('Start client')
            self._battle_window.pubsub_client.start_client(self.server_config.pubsub_path)
            await self._battle_window.pubsub_client.wait_until_ready()
            self.hide()
            print('done')
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            print(f'Failed to open battle window: {repr(exc)}')
        print('Running forever')
        await self._battle_window.pubsub_client.wait_until_done()

    @asyncSlot()
    async def join_match_callback(self):
        # TODO: add a lobby-join screen instead of just taking first game found

        # try joining the first game
        try:
            self.joinMatch.setDisabled(True)
            self.joinMatch.setText("Joining Match...")

            games = await self.client.get_joinable_games()
            if not games:
                error_window("No valid games. Try creating one!")
                return

            resp = await self.client.join_game(games[0], self.user)
            if resp.success:
                # create a lobby window with the START GAME button disabled
                self._lobby_window = LobbyWindow(self, self.user, self.client, game_id=games[0])
                # start subscribing to state updates over pubsub
                self._lobby_window.start_pubsub_subscription()
                print(self.server_config.pubsub_path)
                self._lobby_window.pubsub_client.start_client(self.server_config.pubsub_path)
                await self._lobby_window.pubsub_client.wait_until_ready()
                self._lobby_window.show()
                self.hide()
        except Exception as exc:
            error_window(f'Failed to join game: {repr(exc)}')
        finally:
            self.joinMatch.setDisabled(False)
            self.joinMatch.setText("Join Match")

    @asyncSlot()
    async def config_callback(self):
        print('Opening config window')
