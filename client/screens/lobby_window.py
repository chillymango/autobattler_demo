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
        self.show()

        # player displays
        # TODO: use constant for game size
        self.playerButton: T.Dict[int, QtWidgets.QPushButton] = {}
        for idx in range(8):
            button = self.playerButton[idx] = self.findChild(QtWidgets.QPushButton, f"player{idx}")
            button.setText('---')
            button.setDisabled(True)

        # leave game callback
        self.leaveGame = self.findChild(QtWidgets.QPushButton, "leaveGame")
        self.leaveGame.clicked.connect(self.leave_game_callback)

    def start_pubsub_subscription(self):
        """
        heh
        """
        pubsub_topic = f"pubsub-state-{self.game_id}"
        self.pubsub_client.subscribe(pubsub_topic, callback=self._state_callback)
        print(f'Started pubsub subscription of {pubsub_topic}')

    async def _state_callback(self, topic, data):
        # TODO: dep structure is pretty bad
        print(f'Data: {data}')
        state = State.parse_raw(data)
        print(state.players)
        for idx, player in enumerate(state.players):
            print(player)
            button = self.playerButton[idx]
            button.setText(player.name)
            button.setDisabled(False)

        # TODO: replace 8 with constant
        for num in range(len(state.players), 8):
            print('empty')
            button = self.playerButton[num]
            button.setText("---")
            button.setDisabled(True)

    @asyncSlot()
    async def leave_game_callback(self):
        await self.leave_game()
        self.hide()

    def leave_game_callback(self):
        asyncio.ensure_future(self.leave_game())
        self.hide()  # TODO: holy shit what a hack
        self.parent.show()

    async def leave_game(self):
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