"""
Player Item View
"""
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot
from client.client_env import ClientState
from engine.models.items import ITEM_NAME_LOOKUP, InstantPlayerItem, PlayerItem, PokemonItem, TargetType
from utils.buttons import ItemButton
from utils.websockets_client import WebSocketClient

if T.TYPE_CHECKING:
    from client.screens.battle_window import Ui as BattleWindow
    from engine.env import Environment
    from server.api.user import User
    from utils.context import GameContext


class ItemStaging:
    """
    Semi-persistent object that tracks Pokemon held item and Pokemon combined item.
    """


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
        if self.env is not None:
            self.state: ClientState = env.state
        else:
            self.state = None
        self.ctx = ctx
        self.user = user
        self.websocket: WebSocketClient = websocket
        self._inventory_lookup: T.Dict[int, PokemonItem] = dict()
        self._last_seen_inventory = None
        uic.loadUi('client/qtassets/itemwindow.ui', self)
        self.update_state()

        # instantiate buttons
        self.itemIcon = self.findChild(QtWidgets.QPushButton, "itemIcon")
        self.item_icon_button = ItemButton(self.itemIcon, self.env)
        self.useItem = self.findChild(QtWidgets.QPushButton, "useItem")

        # item view
        self.itemView = self.findChild(QtWidgets.QListView, "itemView")
        self.item_view_model = None

        # connect buttons
        self.useItem.clicked.connect(self.use_item_callback)

        for callback in [
            self.render,
            self.render_selected_item,
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def render(self):
        """
        Render the state after a state update
        """
        # need to do a per-item comparison
        if self._last_seen_inventory is not None:
            if len(self._last_seen_inventory) == len(self.inventory):
                for (x, y) in zip(self._last_seen_inventory, self.inventory):
                    if x != y:
                        break
                else:
                    return
        self._last_seen_inventory = [_ for _ in self.inventory]

        self.render_item_view()

    def update_state(self):
        self.current_player = self.parent.player
        self.env = self.parent.env
        self.state = self.env.state
        self.inventory = self.parent.inventory

    def render_item_view(self):
        """
        Only show items that can be given to Pokemon
        """
        player_items: T.List[PlayerItem] = []
        for item in self.inventory:
            if item.tt == TargetType.PLAYER:
                player_items.append(item)

        print('Doing update of item view')
        self.item_view_model = QtGui.QStandardItemModel()
        for idx, item in enumerate(player_items):
            qitem = QtGui.QStandardItem(ITEM_NAME_LOOKUP.get(item.__class__, item.__class__))
            self.item_view_model.appendRow(qitem)
            self._inventory_lookup[idx] = item
        self.itemView.setModel(self.item_view_model)

    def render_selected_item(self):
        item_selected = self.itemView.selectedIndexes()
        for item_member in item_selected:
            row = item_member.row()
            item = self._inventory_lookup[row]
            self.item_icon_button.set_item(item)

            # if an instant item, go ahead and allow use
            if isinstance(item, InstantPlayerItem):
                self.useItem.setDisabled(False)
            else:
                self.useItem.setDisabled(True)
            break
        else:
            self.item_icon_button.set_item(None)
            self.useItem.setDisabled(True)

    @asyncSlot()
    async def use_item_callback(self):
        """
        Use the currently selected item
        """
        item_selected = self.itemView.selectedIndexes()
        for item_member in item_selected:
            row = item_member.row()
            item = self._inventory_lookup[row]
            await self.websocket.use_item(self.ctx, item_id=item.id)

    def closeEvent(self, *args, **kwargs):
        self.parent.poke_item_window = None
        super().closeEvent(*args, **kwargs)
