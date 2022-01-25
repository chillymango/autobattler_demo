"""
Random item distribution:
* total value of distributed items is shared across all players
* e.g 5 small berries is considered to be equal to 2 large berries and 1 small
* (need to assign points to persistent player items)
"""
import os
import random
import typing as T
from collections import namedtuple
from pydantic import BaseModel

from engine.base import Component
from engine.inventory import PlayerInventoryManager
from engine.items import ItemManager
from engine.models.item_event import ItemSchedule
from engine.models.items import Item
from engine.player import PlayerManager

#TurnConfig = namedtuple("TurnConfig", ["item_set", "score"])


class ItemEventManager(Component):
    """
    Defines and manages the item distribution
    """

    CONFIG_PATH = 'data/default_item_schedule.json'

    @property
    def dependencies(self) -> T.List:
        return [
            ItemManager,
            PlayerInventoryManager,
        ]

    def initialize(self):
        """
        Load data files which define item distribution schedules
        """
        super().initialize()
        
        # TODO: make this more configurable. For now, load the basic 'somewhat variable'
        # default item schedule
        self.item_schedule: ItemSchedule = ItemSchedule.parse_file(self.CONFIG_PATH)

    def turn_setup(self):
        """
        Roll and Distribute items.

        Automatic items should be logged to players.

        Choice items should be presented over the WebSocket connection.
        """
        # if there is no schedule for this turn just skip
        if not self.item_schedule.turn_configs.get(self.state.turn_number):
            return

        pm: PlayerManager = self.env.player_manager
        for player in self.state.players:
            player_items = self.item_schedule.roll_items(self.state.turn_number)
            # TODO: implement choices
            # give items to players
            for item_name in player_items:
                item = pm.create_and_give_item_to_player(player, item_name)
                self.log(f"Received a {item.name}!", recipient=player)
