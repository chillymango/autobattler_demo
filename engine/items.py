"""
Item Manager
"""
import typing as T
from uuid import UUID

from engine.base import Component
from engine.models import items

if T.TYPE_CHECKING:
    from engine.models.pokemon import Pokemon
    from engine.models.player import Player


class ItemSubManager:
    """
    Manages a set of items
    """

    def __init__(self, item_type: T.Type, factory: T.Dict[str, T.Callable]):
        self._item_type = item_type
        self._items: T.Set[items.Item] = set()

        # validate factory
        self.validate_factory(factory)
        self.factory: T.Dict[str, T.Type[items.Item]] = factory

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
            items.InstantPlayerItem,
            items.PersistentPlayerItem,
            items.InstantPokemonItem,
            items.PersistentPokemonItem,
            items.CombatItem,
            items.PlayerHeroPower
        ]

        # TODO: dynamic evaluation
        self.persistent_item_types = (items.PersistentPlayerItem, items.PersistentPokemonItem)
        self.instant_item_types = (items.InstantPlayerItem, items.InstantPokemonItem)

        self._factories: T.Dict[T.Type, T.Dict[str, T.Callable]] = {
            items.InstantPlayerItem: dict(
                master_ball=items.MasterBall,
            ),
            items.PersistentPlayerItem: dict(
                poke_flute=items.PokeFlute,
            ),
            items.InstantPokemonItem: dict(
                fire_stone=items.FireStone,
                water_stone=items.WaterStone,
            ),
            items.CombatItem: dict(
            ),
            items.PersistentPokemonItem: dict(), 
            items.PlayerHeroPower: dict()
        }

        self.submanagers: T.Dict[T.Type, ItemSubManager] = {
            type_: ItemSubManager(type_, self._factories[type_])
            for type_ in self.supported_types
        }
        # create reverse associations for items
        self.id_to_item: T.Dict[UUID, items.Item] = dict()
        self.item_to_manager: T.Dict[str, ItemSubManager] = dict()
        for submgr in self.submanagers.values():
            for item_name in submgr.factory:
                self.item_to_manager[item_name] = submgr

        # expose a mapping of costs for each item
        self.item_costs: T.Dict[str, int] = {}
        for submgr in self.submanagers.values():
            for item_name, item_class in submgr.factory.items():
                # instantiate an ephemeral, immediately consume
                item = item_class(self.env)
                self.item_costs[item_name] = item.cost
                item.consumed = True
                item.delete()

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

    def get_item_class_by_name(self, item_name: str):
        """
        Get the item class for an item

        NOTE: this should be re-evaluated at call time so imported factories will show up
        """
        manager = self.item_to_manager[item_name]
        return manager.factory[item_name]

    def get_item_by_id(self, item_id: T.Union[str, UUID]):
        if isinstance(item_id, str):
            item_id = UUID(item_id)
        return self.id_to_item[item_id]

    def get_item_factory_by_name(self, item_name: str):
        """
        Get the item factory for a specific item name.
        """
        manager = self.item_to_manager[item_name]
        return manager.factory[item_name]

    def create_item(self, item_name: str) -> items.Item:
        """
        Create an item by item name
        """
        # dispatch create request to submanager
        submanager: ItemSubManager = self.item_to_manager[item_name]
        return submanager.factory[item_name](self.env)

    @property
    def combat_items(self) -> T.Set[items.CombatItem]:
        """
        Return a set of all combat items
        """
        return set(
            x for x in self._item_factory[items.PersistentPokemonItem]
            if isinstance(x, items.CombatItem)
        )

    def remove_orphaned_items(self):
        """
        Items that are not in a player inventory or given to a Pokemon are orphaned.

        NOTE: this should just print warnings because it's a sign of sloppy programming
        """
        pass

    def remove_consumed_items(self):
        """
        Check all item lists
        """
        pass

    def turn_setup(self) -> None:
        """
        Run item actions in turn_setup

        Run this only for Persistent items
        """
        for persistent_itype in self.persistent_item_types:
            submgr = self.submanagers[persistent_itype]
            for item in submgr._items:
                item: items.PersistentItemMixin
                item.turn_setup()
        self.remove_consumed_items()

    def turn_execute(self):
        """
        Run item actions in turn_execute

        NOTE: this should run before battle manager executes
        """
        for persistent_itype in self.persistent_item_types:
            submgr = self.submanagers[persistent_itype]
            for item in submgr._items:
                item: items.PersistentItemMixin
                item.turn_execute()
        self.remove_consumed_items()

    def turn_cleanup(self):
        for persistent_itype in self.persistent_item_types:
            submgr: ItemSubManager = self.submanagers[persistent_itype]
            for item in submgr._items:
                item: items.PersistentItemMixin
                item.turn_cleanup()
        self.remove_consumed_items()
        self.remove_orphaned_items()
