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

    def initialize(self):
        """
        Instantiate player / item relationships

        This manager is responsible for updating player inventories as well.
        """
        super().initialize()
        self.player_inventories: T.Dict[Player, T.Set[Item]] = {
            player: player.inventory for player in self.state.players
        }

    def create_and_give_item_to_player(self, item_name: str, player: Player):
        """
        Create an item by item name and give it to a player
        """
        item_manager: ItemManager = self.env.item_manager
        item = item_manager.create_item(item_name)

        # update item state
        self.player_inventories[player].add(item)
        item.holder = player

    def remove_item_from_player(self, item_name: str, player: Player):
        """
        Remove an item by item name from a player
        """
        for item in self.player_inventories[player]:
            if item.name == item_name:
                item.holder = None
                self.player_inventories[player].remove(item)
                return

    def give_item_to_pokemon(self, item: Item, pokemon: Pokemon):
        """
        Move an Item from a player inventory into a Pokemon battle card.

        TODO: implement phase checks to ensure that these ops don't happen during combat
        """
        player: Player = item.holder
        # NOTE: I think we should make these transactions throw exceptions when
        # things we don't expect occur
        if not isinstance(player, Player):
            raise Exception(f"Tried to give item to {pokemon} that wasn't ready to give")

        if pokemon not in player.roster:
            raise Exception(f"{item} does not belong to {player}")

        # after validation checks pass we should move the item out of player inventory, move it
        # into the Pokemon battle card, and then change the item holder
        # NOTE: transactions should be atomic
        pass
