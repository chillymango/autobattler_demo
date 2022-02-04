"""
Manage storage and party
"""
import asyncio
from collections import defaultdict
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot
from engine.models.pokemon import Pokemon

from utils.buttons import PokemonButton
from utils.websockets_client import WebSocketClient

if T.TYPE_CHECKING:
    from client.screens.battle_window import Ui as BattleWindow
    from engine.env import Environment
    from server.api.user import User
    from utils.context import GameContext

class CleanPrinter:
    """
    Print every X occurrences to avoid spamming
    """

    def __init__(self):
        self.every = 10
        self.idx = 0

    def __call__(self, to_print):
        if not self.idx % self.every:
            print(to_print)
        self.idx += 1


printer = CleanPrinter()


class Ui(QtWidgets.QDialog):

    def __init__(
        self,
        parent,
        env: "Environment" = None,
        ctx: "GameContext" = None,
        user: "User" = None,
        websocket = None,
    ):
        super(Ui, self).__init__()
        self.parent: "BattleWindow" = parent
        self.env = env
        self.ctx = ctx
        self.user = user
        self.websocket: WebSocketClient = websocket
        self._last_seen_party = None
        self._last_seen_storage = None
        uic.loadUi('client/qtassets/storage.ui', self)
        # keep the actual Pokemon objects here so they can be referenced by index
        self._party_lookup: T.Dict[int, Pokemon] = defaultdict(lambda: None)
        self._storage_lookup: T.Dict[int, Pokemon] = defaultdict(lambda: None)
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

        # load Pokemon buttons
        self.partyPokemonIcon = self.findChild(QtWidgets.QPushButton, "partyPokemonIcon")
        self.party_pokemon_button = PokemonButton(self.partyPokemonIcon, self.env)
        self.storagePokemonIcon = self.findChild(QtWidgets.QPushButton, "storagePokemonIcon")
        self.storage_pokemon_button = PokemonButton(self.storagePokemonIcon, self.env)

        # run timer for render_buttons
        for callback in [
            self.render_buttons
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def update_state(self):
        self.current_player = self.parent.player
        self.env = self.parent.env

    def render_buttons(self):
        """
        NOTE: will only update the last one if multiple selected but i think that's fine
        """
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            row = party_member.row()
            poke = self._party_lookup[row]
            self.party_pokemon_button.set_pokemon(poke)
            break
        else:
            self.party_pokemon_button.set_pokemon(None)

        storage_selected = self.storageView.selectedIndexes()
        for storage_member in storage_selected:
            row = storage_member.row()
            poke = self._storage_lookup[row]
            self.storage_pokemon_button.set_pokemon(poke)
            break
        else:
            self.storage_pokemon_button.set_pokemon(None)

    def render_party(self, force=False):
        # NOTE: if party didn't change from last update, do not render
        # this is because we screw with the UI targeting if we render every time
        if not force:
            if self._last_seen_party == self.parent.party:
                return
        self._last_seen_party = self.parent.party

        print('Doing update of party')
        self.party_model = QtGui.QStandardItemModel()
        for idx, pokemon in enumerate(self.parent.party):
            # TODO: fix this, what a horrible pattern of potentially accepting nulls
            if pokemon is not None:
                item = QtGui.QStandardItem(str(pokemon))
            else:
                item = QtGui.QStandardItem(pokemon)
            self.party_model.appendRow(item)
            self._party_lookup[idx] = pokemon
        self.partyView.setModel(self.party_model)

    def render_storage(self, force=False):
        # NOTE: if storage didn't change from last update, do not render
        # this is because we screw with the UI targeting if we render every time
        if not force:
            if self._last_seen_storage == self.parent.storage:
                return
        self._last_seen_storage = self.parent.storage

        print('Doing update of storage')
        self.storage_model = QtGui.QStandardItemModel()
        for idx, pokemon in enumerate(self.parent.storage):
            if pokemon is not None:
                item = QtGui.QStandardItem(str(pokemon))
            else:
                item = QtGui.QStandardItem(pokemon)
            self.storage_model.appendRow(item)
            self._storage_lookup[idx] = pokemon
        self.storageView.setModel(self.storage_model)

    @asyncSlot()
    async def move_party_to_storage(self):
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            row = party_member.row()
            party_config = self.current_player.party_config.copy()
            party_config.remove_from_party_by_idx(row)
            await self.websocket.update_party_config(self.ctx, party_config)

    @asyncSlot()
    async def move_storage_to_party(self):
        storage_selected = self.storageView.selectedIndexes()
        # TODO: this currently really just supports 1 moving at a time, maybe fix that
        for storage_member in storage_selected:
            row = storage_member.row()
            poke = self.parent.storage[row]
            party_config = self.current_player.party_config.copy()
            if not party_config.add_to_party(poke.id):
                print(f'Could not move {poke} into party')
            await self.websocket.update_party_config(self.ctx, party_config)

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
            print(f'Releasing from storage {idx}')
            await self.websocket.release_from_storage(self.ctx, idx)

    def closeEvent(self, *args, **kwargs):
        self.parent.storage_window = None
        super().closeEvent(*args, **kwargs)
