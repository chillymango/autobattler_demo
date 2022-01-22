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
from engine.models.items import Item

#TurnConfig = namedtuple("TurnConfig", ["item_set", "score"])


class ItemEventManager(Component):
    """
    Defines and manages the item distribution
    """

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
        # read item schedules from JSON
