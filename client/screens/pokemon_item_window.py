"""
Pokemon-specific item view

Only one window should be active at a time.
List should only render Pokemon items.
"""
import typing as T
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from qasync import asyncSlot
from client.client_env import ClientState
from engine.models.items import ITEM_NAME_LOOKUP, ItemName, PokemonItem, TargetType, get_item_class_by_name
from engine.models.pokemon import Pokemon

from utils.buttons import ItemButton, PokemonButton
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
        pokemon: Pokemon = None,
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
        self.pokemon = pokemon
        self.websocket: WebSocketClient = websocket
        self._inventory_lookup: T.Dict[int, PokemonItem] = dict()
        self._last_seen_inventory = None
        uic.loadUi('client/qtassets/pokeitemwindow.ui', self)
        self.update_state()

        # track stuff
        self.primary_item = None
        self.combine_item = None

        # instantiate buttons
        self.pokemonIcon = self.findChild(QtWidgets.QPushButton, "pokemonIcon")
        self.pokemonLabel = self.findChild(QtWidgets.QLabel, "pokemonLabel")
        self.removePrimary = self.findChild(QtWidgets.QPushButton, "removePrimary")
        self.invToPrimary = self.findChild(QtWidgets.QPushButton, "invToPrimary")
        self.invToCombine = self.findChild(QtWidgets.QPushButton, "invToCombine")
        self.combineItems = self.findChild(QtWidgets.QPushButton, "combineItems")
        self.itemIcon = self.findChild(QtWidgets.QPushButton, "itemIcon")
        self.primaryIcon = self.findChild(QtWidgets.QPushButton, "primaryIcon")
        self.combineIcon = self.findChild(QtWidgets.QPushButton, "combineIcon")

        self.pokemon_icon_button = PokemonButton(self.pokemonIcon, self.env, label=self.pokemonLabel)
        self.primary_icon_button = ItemButton(self.primaryIcon, self.env)
        self.item_icon_button = ItemButton(self.itemIcon, self.env)
        self.combine_icon_button = ItemButton(self.combineIcon, self.env)

        # item view
        self.itemView = self.findChild(QtWidgets.QListView, "itemView")
        self.item_view_model = None

        # connect buttons
        self.removePrimary.clicked.connect(self.remove_primary_callback)
        self.invToPrimary.clicked.connect(self.inv_to_primary_callback)
        self.invToCombine.clicked.connect(self.inv_to_combine_callback)
        self.combineItems.clicked.connect(self.combine_items_callback)

        for callback in [
            self.render,
            self.render_selected_item,
            self.render_item_buttons
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        if self.pokemon is not None:
            self.render_pokemon()
            self.render_item_view()
            self.show()

    def reload(self, pokemon: Pokemon):
        """
        Point the UI at a new Pokemon and show it
        """
        self._item_staging = ItemStaging()
        self.set_pokemon(pokemon)
        self.update_state()
        self.render()

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
        self.render_pokemon()

    def set_pokemon(self, pokemon: Pokemon):
        """
        If this doesn't get set, the window will not show.
        """
        self.pokemon = pokemon

    def update_state(self):
        if self.pokemon is None:
            self.hide()
            return

        self.current_player = self.parent.player
        self.env = self.parent.env
        self.state = self.env.state
        self.inventory = self.parent.inventory

    def render_pokemon(self):
        self.pokemon_icon_button.render_pokemon_card(self.pokemon)

    def render_item_view(self):
        """
        Only show items that can be given to Pokemon
        """
        poke_items: T.List[PokemonItem] = []
        for item in self.inventory:
            if item.tt == TargetType.POKEMON:
                poke_items.append(item)

        print('Doing update of item view')
        self.item_view_model = QtGui.QStandardItemModel()
        for idx, item in enumerate(poke_items):
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
            break
        else:
            self.item_icon_button.set_item(None)

    def _get_primary_item(self):
        """
        If Pokemon is holding an item, return it.
        """
        poke_held_item_raw = self.state.pokemon_held_items_raw.get(self.pokemon.id)
        if poke_held_item_raw is not None:
            item_name = ItemName(poke_held_item_raw.name).name
            item_class = get_item_class_by_name(item_name)
            return item_class(self.env, id=poke_held_item_raw.id)
        return None

    def render_item_buttons(self):
        """
        Check if the Pokemon target has an equipped item or not.

        Render the item icon if it does.

        Also render the combine staging item.
        """
        self.primary_icon_button.set_item(self._get_primary_item())

        if self.combine_item is not None:
            self.combine_icon_button.set_item(self.combine_item)
        else:
            self.combine_icon_button.clear()

    @asyncSlot()
    async def inv_to_primary_callback(self):
        """
        Take the selected item and equip it to Pokemon.

        This should be done via API request to ensure the backend acknowledges the request.
        """
        print('Running inv_to_primary')
        item_selected = self.itemView.selectedIndexes()
        # TODO: this currently really just supports 1 moving at a time, maybe fix that
        for item_member in item_selected:
            item = self._inventory_lookup[item_member.row()]
            await self.websocket.give_item_to_pokemon(self.ctx, item.id, self.pokemon.id)
        self.render()

    def inv_to_combine_callback(self):
        """
        Take the selected item and move it into the Combine staging area.

        This is only done locally.
        """
        print('Running inv_to_combine')
        item_selected = self.itemView.selectedIndexes()
        for item_member in item_selected:
            item = self._inventory_lookup[item_member.row()]
            self.combine_item = item
        self.render()

    @asyncSlot()
    async def remove_primary_callback(self):
        """
        Remove the Pokemon's selected item.

        This should be done via API request.
        """
        print('Running remove_primary')
        await self.websocket.remove_item_from_pokemon(self.ctx, self.pokemon.id)
        self.render()

    @asyncSlot()
    async def combine_items_callback(self):
        """
        Issue a request to combine items.

        This should be done via API request.
        """
        print('Running combine items.')
        # get primary from Pokemon holder
        primary_item = self._get_primary_item()
        if primary_item is None:
            print('No primary item to combine.')
            return

        secondary_item = self.combine_item
        if secondary_item is None:
            print('No secondary item to combine.')
            return

        await self.websocket.combine_items(self.ctx, primary_item.id, secondary_item.id)

        self.combine_item = None
        self.render()

    def closeEvent(self, *args, **kwargs):
        self.parent.poke_item_window = None
        super().closeEvent(*args, **kwargs)
