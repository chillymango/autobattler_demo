"""
Manage storage and party
"""
from os import error
from IPython.core.application import IPYTHON_SUPPRESS_CONFIG_ERRORS
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic


class Ui(QtWidgets.QDialog):

    def __init__(self, game_state=None):
        super(Ui, self).__init__()
        self.state = game_state
        uic.loadUi('qtassets/storage.ui', self)

        self.update_party_signal = QtCore.pyqtSignal()
        #self.update_party_signal.connect(self.render_party)

        self.update_storage_signal = QtCore.pyqtSignal()
        #self.update_storage_signal.connect(self.render_storage)

        self.current_player = self.state.current_player

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

    def render_party(self):
        self.party_model = QtGui.QStandardItemModel()
        for pokemon in self.current_player.party:
            # TODO: fix this, what a horrible pattern of potentially accepting nulls
            if pokemon is not None:
                item = QtGui.QStandardItem(pokemon.name)
            else:
                item = QtGui.QStandardItem(pokemon)
            self.party_model.appendRow(item)
        self.partyView.setModel(self.party_model)

    def render_storage(self):
        self.storage_model = QtGui.QStandardItemModel()
        for pokemon in self.current_player.storage:
            if pokemon is not None:
                item = QtGui.QStandardItem(pokemon.name)
            else:
                item = QtGui.QStandardItem(pokemon)
            self.storage_model.appendRow(item)
        self.storageView.setModel(self.storage_model)

    def move_party_to_storage(self):
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            row = party_member.row()
            pokemon = self.current_player.party[row]
            self.current_player.party[row] = None
            self.current_player.storage.append(pokemon)
        self.render_party()
        self.render_storage()

    def move_storage_to_party(self):
        storage_selected = self.storageView.selectedIndexes()
        # TODO: this currently really just supports 1 moving at a time, maybe fix that
        for storage_member in storage_selected:
            if self.current_player.party_is_full:
                print("Out of space in party")
                break

            row = storage_member.row()
            pokemon = self.current_player.storage[row]
            self.current_player.storage.remove(pokemon)
            self.current_player.add_to_party(pokemon)
        self.render_party()
        self.render_storage()

    def release_pokemon_party(self):
        party_selected = self.partyView.selectedIndexes()
        for party_member in party_selected:
            idx = party_member.row()
            self.current_player.release_from_party(idx)
        self.render_party()

    def release_pokemon_storage(self):
        storage_selected = self.storageView.selectedIndexes()
        for storage_member in storage_selected:
            idx = storage_member.row()
            self.current_player.release_from_storage(idx)
        self.render_storage()
