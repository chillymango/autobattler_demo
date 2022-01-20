"""
Item Manager
"""
import typing as T

from engine.base import Component
from engine.models.items import Berry, InstantPlayerItem, PersistentPlayerItem, PersistentPokemonItem
from engine.models.items import CombatItem
from engine.models.items import InstantPokemonItem
from engine.models.items import Item
from engine.models.items import MasterBall
from engine.models.items import PlayerItem
from engine.models.items import PokeFlute
from engine.models.items import PokemonItem
from engine.models.items import Stone
from engine.player import PlayerManager

if T.TYPE_CHECKING:
    from engine.models.pokemon import Pokemon
    from engine.models.player import Player


class ItemSubManager:
    """
    Manages a set of items
    """

    def __init__(self, item_type: T.Type, factory: T.Dict[str, T.Callable]):
        self._item_type = item_type
        self._items: T.Set = set()

        # validate factory
        self.validate_factory(factory)
        self.factory: T.Dict[str, T.Callable] = factory

    def validate_factory(self, factory) -> None:
        for factory_method in factory.values():
            if not isinstance(factory_method(), self.ITEMTYPE):
                raise Exception("Invalid factory method")


class ItemManager(Component):
    """
    Manage items and their relationships to players and Pokemon
    """

    def initialize(self):
        # set up submanagers
        self._items = set()
        self.supported_types = [
            InstantPlayerItem,
            PersistentPlayerItem,
            InstantPokemonItem,
            PersistentPokemonItem,
        ]
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
            PersistentPokemonItem: dict(
                oran_berry=Berry.oran_berry_factory,
            )
        }

        self.submanagers: T.Dict[T.Type, ItemSubManager] = {
            type_: ItemSubManager(type_, self._factories[type_])
            for type_ in self.supported_types
        }
        # create reverse associations for items
        self.item_to_manager: T.Dict[str, ItemSubManager] = dict()
        for submgr in self.submanagers.values():
            for item_name in submgr.factory:
                self.item_to_manager[item_name] = submgr

    def create_item(self, item_name: str) -> Item:
        """
        Create an item by item name
        """
        # dispatch create request to submanager
        submanager: ItemSubManager = self.item_to_manager[item_name]
        item = submanager.factory[item_name](self.env)
        self._items.add(item)
        return item

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
        for item_set in self._items.values():
            for item in item_set:
                if isinstance(item, PokemonItem):
                    if item.pokemon is None and item.player is None:
                        print(f'Item {item} was orphaned and sad')
                        item_set.remove(item)
                elif isinstance(item, PlayerItem):
                    if item.player is None:
                        print(f'Item {item} was orphaned and sad')
                        item_set.remove(item)

    def remove_consumed_items(self):
        """
        Check all item lists
        """
        for items in self._items.values():
            self._remove_consumed_from_item_list(items)

    def _remove_consumed_from_item_list(self, items: T.Set[Item]):
        for item in items:
            if item.consumed:
                items.remove(item)
                if isinstance(item, PokemonItem):
                    if item.pokemon is not None:
                        item.pokemon.berry = None
                elif isinstance(item, PlayerItem):
                    if item.player is not None:
                        item.player.inventory.remove(item)
                        item.player = None

    def create_item(self, item_name: str):
        """
        Instantiate an item object

        Items should be created with this interface as a factory and get assigned to the correct
        list. This way the correct list of item callbacks can be grabbed when running game state
        changes during phase updates.
        """
        if item_name not in self._item_factory:
            raise Exception(f"Unsupported item {item_name}")
        instant = self._item_factory[item_name]()
        if isinstance(instant, PokemonItem):
            self._pokemon_items.add(instant)
        elif isinstance(instant, PlayerItem):
            self._player_items.add(instant)
        return instant

    def create_item_for_player(self, item_name: str, player: "Player"):
        """
        Create an item and give it to a player
        """
        item = self.create_item(item_name)
        # giving logic happens here
        item.player = player
        player.inventory.add(item)

    def give_item_to_pokemon(self, item: PokemonItem, pokemon: "Pokemon", force: bool = False):
        """
        Give an item to a Pokemon from a player inventory

        When this happens, remove it from player inventory.
        """
        # check if pokemon is already holding an item, and force it back into player inventory if
        # specified to do so
        player_manager: PlayerManager = self.env.player_manager
        if pokemon.battle_card.berry:
            if not force:
                raise Exception(f"Pokemon {pokemon.nickname} is already holding an item")
            removed_item = pokemon.battle_card.berry
            # send back to player inventory
            pokemon_holder = player_manager.get_pokemon_holder(pokemon)
            pokemon_holder.inventory.add(removed_item)

        # set object relationships and remove item from player
        pokemon.battle_card.berry = item
        item.pokemon = pokemon

    def create_item_for_pokemon(self, item_name: str, pokemon: "Pokemon"):
        """
        Create an item and give it to a pokemon
        """
        item = self.create_item(item_name)
        # giving logic happens here
        item.pokemon = pokemon
        pokemon.battle_card.berry = item

    def use_instant_pokemon_item(self, item: InstantPokemonItem, pokemon: "Pokemon" = None):
        if pokemon is not None:
            item.pokemon = pokemon
        if item.pokemon is None:
            raise Exception("Item not assigned to anyone")
        item.use()
        # mark as consumed if successful
        # cleanup collection should remove reference from Pokemon
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
        self.remove_orphaned_items()
