"""
Inside a game lobby
"""
import asyncio
import typing as T

from fastapi_websocket_pubsub import PubSubClient
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncClose
from qasync import asyncSlot

from engine.models.state import State
from engine.models.phase import GamePhase

if T.TYPE_CHECKING:
    from utils.client import AsynchronousServerClient
    from server.api.user import User
    from engine.models.state import State


class Ui(QtWidgets.QDialog):
    """
    Game Lobby Display

    Shows other players in the lobby. Provides a `Start Game` button.

    TODO: make start button only available to host
    """

    def __init__(
        self,
        parent: QtWidgets.QMainWindow,
        user: "User",
        client: "AsynchronousServerClient",
        game_id: str,
    ):
        super(Ui, self).__init__()
        self.parent = parent
        self.user: "User" = user
        self.game_id = game_id
        self.client: "AsynchronousServerClient" = client
        uic.loadUi('client/qtassets/lobby.ui', self)
        self.pubsub_client = PubSubClient()

        # player displays
        # TODO: use constant for game size
        self.playerButton: T.Dict[int, QtWidgets.QPushButton] = {}
        for idx in range(8):
            button = self.playerButton[idx] = self.findChild(QtWidgets.QPushButton, f"player{idx}")
            button.setText('---')
            button.setDisabled(True)

        # start game
        self.startGame = self.findChild(QtWidgets.QPushButton, "startGame")
        self.startGame.clicked.connect(self.start_game_callback)
        self.lobbyStatus = self.findChild(QtWidgets.QLabel, "lobbyStatus")

        # leave game
        self.leaveGame = self.findChild(QtWidgets.QPushButton, "leaveGame")
        self.leaveGame.clicked.connect(self.leave_game_callback)

    def start_pubsub_subscription(self):
        pubsub_topic = f"pubsub-state-{self.game_id}"
        self.pubsub_client.subscribe(pubsub_topic, callback=self._state_callback)
        print(f'Started pubsub subscription of {pubsub_topic}')

    async def _state_callback(self, topic, data):
        state = State.parse_raw(data)

        # if game is no longer in INITIALIZATION, open the battle window
        if state.phase not in [GamePhase.ERROR, GamePhase.COMPLETED, GamePhase.INITIALIZATION]:
            print('STARTING A GAME...')
            self.lobbyStatus.setText("Starting game...")
            # TODO: not sure if this is the correct pattern...
            try:
                print('Disconnecting pubsub')
                await self.pubsub_client.disconnect()
                print('Disconnected pubsub')
            except BaseException as exc:
                print('In EXC handler')
                print(repr(exc))

            print('Opening BW')
            await self.parent.open_battle_window()
            self.hide()
            return

        for idx, player in enumerate(state.players):
            button = self.playerButton[idx]
            button.setText('\n'.join(player.name.split()))
            button.setDisabled(False)

        # TODO: replace 8 with constant
        for num in range(len(state.players), 8):
            button = self.playerButton[num]
            button.setText("---")
            button.setDisabled(True)

        # if current player is player0, give them the start button control
        if state.players and state.players[0].id == self.user.id:
            self.startGame.setDisabled(False)
        else:
            self.startGame.setDisabled(True)

    @asyncSlot()
    async def start_game_callback(self):
        try:
            self.startGame.setDisabled(True)
            self.lobbyStatus.setText("Starting Game...")
            try:
                await self.client.start_game(self.game_id)
            except Exception as exc:
                print(repr(exc))
            # defer transition trigger to state callback
        finally:
            self.startGame.setDisabled(False)

    @asyncSlot()
    async def leave_game_callback(self):
        await self.leave_game()

    def leave_game_callback(self):
        asyncio.ensure_future(self.leave_game())
        self.hide()  # TODO: holy shit what a hack
        self.parent.show()

    async def leave_game(self):
        await self.pubsub_client.disconnect()
        await self.client.leave_game(self.game_id, self.user)

    @asyncClose
    async def closeEvent(self, *args, **kwargs):
        self.parent.show()
        await self.leave_game()
        super().closeEvent(*args, **kwargs)


if __name__ == "__main__":
    import sys
    from uuid import uuid4
    from utils.client import AsynchronousServerClient
    from server.api.user import User
    app = QtWidgets.QApplication(sys.argv)
    user = User(name='Albert Yang', id=str(uuid4()))
    client = None
    window = Ui(user=user, client=client)
    app.exec_()
