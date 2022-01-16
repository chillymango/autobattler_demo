"""
Manage storage and party
"""
from locale import currency
from telnetlib import IP
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot

from utils.websockets_client import WebSocketClient

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.player import Player
    from server.api.player import Player as PlayerModel
    from utils.context import GameContext


class Ui(QtWidgets.QDialog):

    def __init__(
        self,
        parent,
        env: "Environment" = None,
        ctx: "GameContext" = None,
        player_model: "PlayerModel" = None,
        websocket = None,
    ):
        super(Ui, self).__init__()
        self.parent = parent
        self.env = env
        self.ctx = ctx
        self.player_model = player_model
        self.websocket: WebSocketClient = websocket
        self._last_seen_party = None
        self._last_seen_storage = None
        uic.loadUi('client/qtassets/storage.ui', self)
        self.update_state()

        # load current party
        self.partyView = self.findChild(QtWidgets.QListView, "partyView")
        self.render_party()

        # load current storage
        self.storageView = self.findChild(QtWidgets.QListView, "storageView")
        self.render_storage()

        # support moving pokemon
        self.partyToStorage = self.findChild(QtWidgets.QPushButton, "partyToStorage")
        self.partyToStorage.clicked.connect(self.move_party_to_storage)

        self.storageToParty = self.findChild(QtWidgets.QPushButton, "storageToParty")
        self.storageToParty.clicked.connect(self.move_storage_to_party)

        # support release buttons
        self.releaseParty = self.findChild(QtWidgets.QPushButton, "releaseParty")
        self.releaseParty.clicked.connect(self.release_pokemon_party)
        self.releaseStorage = self.findChild(QtWidgets.QPushButton, "releaseStorage")
        self.releaseStorage.clicked.connect(self.release_pokemon_storage)

        self.show()

    def update_state(self):
        try:
            self.current_player = self.env.state.get_player_by_id(self.player_model.id)
        except Exception as exc:
            print(repr(exc))

    def render_party(self):
        # NOTE: if party didn't change from last update, do not render
        # this is because we screw with the UI targeting if we render every time
        if self._last_seen_party == self.current_player.party:
            return
        self._last_seen_party = self.current_player.party

        self.party_model = QtGui.QStandardItemModel()
        for pokemon in self.current_player.party:
            # TODO: fix this, what a horrible pattern of potentially accepting nulls
            if pokemon is not None:
                item = QtGui.QStandardItem(str(pokemon))
            else:
                item = QtGui.QStandardItem(pokemon)
            self.party_model.appendRow(item)
        self.partyView.setModel(self.party_model)

    def render_storage(self):
        # NOTE: if storage didn't change from last update, do not render
        # this is because we screw with the UI targeting if we render every time
        if self._last_seen_storage == self.current_player.storage:
            return
        self._last_seen_storage = self.current_player.storage

        self.storage_model = QtGui.QStandardItemModel()
        for pokemon in self.current_player.storage:
            if pokemon is not None:
                item = QtGui.QStandardItem(str(pokemon))
            else:
                item = QtGui.QStandardItem(pokemon)
            self.storage_model.appendRow(item)
        self.storageView.setModel(self.storage_model)

    @asyncSlot()
    async def move_party_to_storage(self):
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            row = party_member.row()
            await self.websocket.move_to_storage(self.ctx, row)

    @asyncSlot()
    async def move_storage_to_party(self):
        storage_selected = self.storageView.selectedIndexes()
        # TODO: this currently really just supports 1 moving at a time, maybe fix that
        for storage_member in storage_selected:
            row = storage_member.row()
            await self.websocket.move_to_party(self.ctx, row)

    @asyncSlot()
    async def release_pokemon_party(self):
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            idx = party_member.row()
            await self.websocket.release_from_party(self.ctx, idx)

    @asyncSlot()
    async def release_pokemon_storage(self):
        storage_selected = self.storageView.selectedIndexes()
        for storage_member in storage_selected:
            idx = storage_member.row()
            await self.websocket.release_from_storage(self.ctx, idx)

    def closeEvent(self, *args, **kwargs):
        self.parent.storage_window = None
        super().closeEvent(*args, **kwargs)
