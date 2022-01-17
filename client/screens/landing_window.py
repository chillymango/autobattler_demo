"""
Landing Screen

Player will choose to create or join a game from here.
"""
import asyncio
from distutils.log import error
import typing as T

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot

from client.screens.lobby_window import Ui as LobbyWindow
from server.api.lobby import CreateGameResponse
from utils.error_window import error_window
from utils.server_config import ServerConfig

if T.TYPE_CHECKING:
    from utils.client import AsynchronousServerClient
    from server.api.user import User


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
            self.hide()
            await self._lobby_window.pubsub_client.wait_until_done()
        except Exception as exc:
            error_window(str(exc))
        finally:
            self.createMatch.setDisabled(False)
            self.createMatch.setText("Create Match")

    @asyncSlot()
    async def join_match_callback(self):
        # TODO: add a lobby-join screen instead of just taking first game found
        self.joinMatch.setDisabled(True)
        self.joinMatch.setText("Joining Match...")

        attempts = 0
        attempted = set()
        joined_game = False
        while attempts < 3:
            attempts += 1
            games = await self.client.get_joinable_games()
            if not games:
                error_window("No valid games. Try creating one!")
                return

            # try joining the first game
            try:
                resp = await self.client.join_game(games[0], self.user)
                if resp.success:
                    joined_game = True
                    # create a lobby window with the START GAME button disabled
                    self._lobby_window = LobbyWindow(self, self.user, self.client, game_id=games[0])
                    # start subscribing to state updates over pubsub
                    self._lobby_window.start_pubsub_subscription()
                    print(self.server_config.pubsub_path)
                    self._lobby_window.pubsub_client.start_client(self.server_config.pubsub_path)
                    self.hide()
                    await self._lobby_window.pubsub_client.wait_until_done()
            except Exception as exc:
                print(repr(exc))
                await asyncio.sleep(1.0)
            finally:
                self.joinMatch.setDisabled(False)
                self.joinMatch.setText("Join Match")

        if not joined_game:
            error_window("Failed to join a game.")

    @asyncSlot()
    async def config_callback(self):
        print('Opening config window')
