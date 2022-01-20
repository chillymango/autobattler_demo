"""
Item Manager
"""
import typing as T
from uuid import UUID

from engine.base import Component
from engine.models.items import Berry, InstantPlayerItem, PersistentItemMixin, PersistentPlayerItem, PersistentPokemonItem
from engine.models.items import CombatItem
from engine.models.items import InstantPokemonItem
from engine.models.items import Item
from engine.models.items import MasterBall
from engine.models.items import PlayerItem
from engine.models.items import PokeFlute
from engine.models.items import PokemonItem
from engine.models.items import Stone

if T.TYPE_CHECKING:
    from engine.models.pokemon import Pokemon
    from engine.models.player import Player


class ItemSubManager:
    """
    Manages a set of items
    """

    def __init__(self, item_type: T.Type, factory: T.Dict[str, T.Callable]):
        self._item_type = item_type
        self._items: T.Set[Item] = set()

        # validate factory
        self.validate_factory(factory)
        self.factory: T.Dict[str, T.Callable] = factory

    def validate_factory(self, factory) -> None:
        for factory_method in factory.values():
            # use a mock fillin for env
            env = None
            if not isinstance(factory_method(env), self._item_type):
                raise Exception("Invalid factory method")


class ItemManager(Component):
    """
    Manage items and their relationships to players and Pokemon
    """

    ENV_PROXY = "item"

    def initialize(self):
        # set up submanagers
        self.supported_types = [
            InstantPlayerItem,
            PersistentPlayerItem,
            InstantPokemonItem,
            PersistentPokemonItem,
            CombatItem,
        ]

        # TODO: dynamic evaluation
        self.persistent_item_types = (PersistentPlayerItem, PersistentPokemonItem)
        self.instant_item_types = (InstantPlayerItem, InstantPokemonItem)

        self._factories: T.Dict[T.Type, T.Dict[str, T.Callable]] = {
            InstantPlayerItem: dict(
                master_ball=MasterBall,
            ),
            PersistentPlayerItem: dict(
                poke_flute=PokeFlute,
            ),
            InstantPokemonItem: dict(
                fire_stone=Stone.fire_stone_factory,
                water_stone=Stone.water_stone_factory,
            ),
            CombatItem: dict(
                oran_berry=Berry.oran_berry_factory,
            ),
            PersistentPokemonItem: dict()
        }

        self.submanagers: T.Dict[T.Type, ItemSubManager] = {
            type_: ItemSubManager(type_, self._factories[type_])
            for type_ in self.supported_types
        }
        # create reverse associations for items
        self.id_to_item: T.Dict[UUID, Item] = dict()
        self.item_to_manager: T.Dict[str, ItemSubManager] = dict()
        for submgr in self.submanagers.values():
            for item_name in submgr.factory:
                self.item_to_manager[item_name] = submgr

    def import_factory(self, itemtype: T.Type, factory: T.Dict[str, T.Callable]):
        """
        Import a factory specification for an itemtype
        """
        submgr = self.submanagers[itemtype]
        submgr.factory.update(factory)
        for item_name in factory:
            self.item_to_manager[item_name] = submgr

    @property
    def supported_items(self):
        return list(self.item_to_manager.keys())

    def get_item_by_id(self, item_id: T.Union[str, UUID]):
        if isinstance(item_id, str):
            item_id = UUID(item_id)
        return self.id_to_item[item_id]

    def create_item(self, item_name: str) -> Item:
        """
        Create an item by item name
        """
        # dispatch create request to submanager
        submanager: ItemSubManager = self.item_to_manager[item_name]
        item: Item = submanager.factory[item_name](self.env)
        submanager._items.add(item)
        self.id_to_item[item.id] = item
        return item

    def remove_item(self, item: Item) -> None:
        """
        Remove an item from existence
        """
        submanager: ItemSubManager = self.item_to_manager[item.name]
        submanager._items.remove(item)
        self.id_to_item.pop(item.id)

    @property
    def combat_items(self) -> T.Set[CombatItem]:
        """
        Return a set of all combat items
        """
        return set(
            x for x in self._item_factory[PersistentPokemonItem] if isinstance(x, CombatItem)
        )

    def remove_orphaned_items(self):
        """
        Items that are not in a player inventory or given to a Pokemon are orphaned.

        NOTE: this should just print warnings because it's a sign of sloppy programming
        """
        for submgr in self.submanagers.values():
            for item in submgr._items:
                if item.holder is None:
                    print(f'Item {item} was orphaned and sad')
                    self.remove_item(item)

    def remove_consumed_items(self):
        """
        Check all item lists
        """
        for submgr in self.submanagers.values():
            for item in submgr._items:
                if item.consumed:
                    self.remove_item(item)

    def turn_setup(self) -> None:
        """
        Run item actions in turn_setup

        Run this only for Persistent items
        """
        for persistent_itype in self.persistent_item_types:
            for submgr in self.submanagers[persistent_itype]:
                submgr: ItemSubManager
                for item in submgr._items:
                    item: PersistentItemMixin
                    item.turn_setup()
        self.remove_consumed_items()

    def turn_execute(self):
        """
        Run item actions in turn_execute

        NOTE: this should run before battle manager executes
        """
        for persistent_itype in self.persistent_item_types:
            for submgr in self.submanagers[persistent_itype]:
                submgr: ItemSubManager
                for item in submgr._items:
                    item: PersistentItemMixin
                    item.turn_execute()
        self.remove_consumed_items()

    def turn_cleanup(self):
        for persistent_itype in self.persistent_item_types:
            for submgr in self.submanagers[persistent_itype]:
                submgr: ItemSubManager
                for item in submgr._items:
                    item: PersistentItemMixin
                    item.turn_cleanup()
        self.remove_consumed_items()
        self.remove_orphaned_items()
