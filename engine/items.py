"""
Item Manager
"""
import typing as T

from engine.base import Component
from engine.models.items import Item
from engine.models.items import PokemonItem

if T.TYPE_CHECKING:
    from engine.models.pokemon import Pokemon


class ItemManager(Component):
    """
    Manage items
    """

    def initialize(self):
        self._player_items: T.List[Item] = []
        self._pokemon_items: T.List[Item] = []

        # input all types of items

    def remove_consumed_items(self):
        """
        Check all item lists
        """
        self._remove_consumed_from_item_list(self._player_items)
        self._remove_consumed_from_item_list(self._pokemon_items)

    def _remove_consumed_from_item_list(self, item_list: T.List[Item]):
        for item in item_list:
            if item.consumed:
                item_list.remove(item)

    def create_item(self, item_name):
        """
        Instantiate an item object

        Items should be created with this interface as a factory and get assigned to the correct
        list. This way the correct list of item callbacks can be grabbed when running game state
        changes during phase updates.
        """
        # TODO: implement LOL

    def use_instant_pokemon_item(self, item: PokemonItem, pokemon: Pokemon = None):
        if item.pokemon is None and pokemon is None:
            raise Exception("Item not assigned to anyone")
        item.use()
        # mark as consumed if successful
        item.consumed = True

    def assign_item_to_pokemon(self, item: PokemonItem, pokemon: Pokemon):
        if not isinstance(item, PokemonItem):
            raise Exception("Invalid assignment request")
        # TODO: update pokemon with item object

    def turn_setup(self):
        """
        Run item actions in turn_setup
        """
        for item in self._player_items:
            item.turn_setup()
        self.remove_consumed_items()

    def turn_execute(self):
        """
        Run item actions in turn_execute

        NOTE: this should run before battle manager executes
        """
        for item in self._player_items:
            item.turn_execute()
        self.remove_consumed_items()

    def turn_cleanup(self):
        for item in self._player_items:
            item.turn_cleanup()
        self.remove_consumed_items()
