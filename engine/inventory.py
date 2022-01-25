"""
Player inventory manager
"""
import typing as T
from engine.base import Component
from engine.items import ItemManager
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.models.items import Item


class PlayerInventoryManager(Component):
    """
    Manages relationships between players and items
    """

    ENV_PROXY = "inventory_manager"

    def dependencies(self) -> T.List:
        return [
            ItemManager,  # need to build items with this
        ]

    def initialize(self):
        """
        Instantiate player / item relationships

        This manager is responsible for updating player inventories as well.
        """
        super().initialize()
        self.player_inventories: T.Dict[Player, T.Set[Item]] = {
            player: player.inventory for player in self.state.players
        }
