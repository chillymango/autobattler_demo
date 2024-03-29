"""
Abstract Base Classes for Mapping and Containers
"""
import json
import typing as T
from collections import abc
from pydantic import BaseModel

if T.TYPE_CHECKING:
    from engine.models.player import Player
# i have no idea what i'm doing here please help

class PlayerAssociatedContainer(abc.MutableSequence):
    """
    Generic base class that implements MutableSequence abstract base class to provide
    relationship association between player and some object a player is determined to `own`.

    Intended for use in the pokemon party and pokemon storage.
    """

    def __init__(self, size=None):
        self.size = size

    def _check_unique(self, value):
        """
        Check if the value is already in the list
        """
        if value in self.list:
            print(self.list)
            raise ValueError(f"{value} is already in list {self}")

    def _check_size(self):
        if self.size and len(self) >= self.size:
            raise IndexError(f"Size of list exceeded (max allowed is {self.size})")

    def __len__(self):
        return len(self.list)

    def __getitem__(self, index):
        return self.list[index]

    def __setitem__(self, index, value):
        self._check_unique(value)
        self.list[index] = value
        value.player = self.player

    def __delitem__(self, index):
        if self.list[index] is not None:
            self.list[index].player = None
        del self.list[index]

    def insert(self, index, value):
        self._check_size()
        if self.list[index] == value:
            return
        self._check_unique(value)
        self.index.insert(index, value)
        value.player = self.player

    def append(self, value):
        self._check_unique(value)
        if len(self.list) >= self.size:
            raise ValueError("Container size exceeded")
        self.list.append(value)
        value.player = self.player


class PokemonStorage(PlayerAssociatedContainer):
    """
    On adding Pokemon into storage or removing from storage, should update the `player` field
    in the Pokemon to reflect the update.

    All additions must be unique.
    """

    player: "Player"
    size: int
    list: T.List

    def __init__(self, player, size):
        self.player = player
        self.size = size
        self.list = []


class PokemonParty(PlayerAssociatedContainer):
    """
    Fixed-size mutable sequence that implements association between player and pokemon
    """

    player: "Player"
    size: int
    list: T.List

    def __init__(self, player, size):
        self.player = player
        self.size = size
        self.list = [None] * size

    def __len__(self):
        return self.size - sum(x is None for x in self.list)

    def append(self, value):
        """
        Find the first non-None value and set that
        """
        self._check_size()
        self._check_unique(value)
        for idx, item in enumerate(self.list):
            if item is None:
                self.list[idx] = value
                value.player = self.player
                break

    def remove(self, value):
        """
        Find the value and just set it to None
        """
        if value not in self.list:
            raise ValueError(f"{value} not in list")
        idx = self.list.index(value)
        self.list[idx] = None
        value.player = None

    def insert(self, index, value):
        self._check_size()
        self._check_unique(value)
        self.list.insert(index, value)
        self.list = self.list[:-1]
        value.player = self.player

    def __delitem__(self, index):
        """
        Set it to none and remove the relationship
        """
        if self.list[index] is not None:
            self.list[index].player = None
            self.list[index] = None


class PlayerInventory(abc.MutableSet):
    """
    Unordered association of items to players
    """

    def __init__(self, player):
        self.player = player
        self.set = set()

    def __contains__(self, value):
        return value in self.set

    def __iter__(self):
        return iter(self.set)

    def __len__(self):
        return len(self.set)

    def add(self, item):
        # when adding an item to the registry, assign a reference to player
        self.set.add(item)
        item.player = self.player

    def discard(self, item):
        if item in self.set:
            item.player = None
            self.set.remove(item)

    def remove(self, item):
        if item not in self.set:
            raise ValueError(f"Item {item} not in inventory")
        self.discard(item)


if __name__ == "__main__":
    import IPython; IPython.embed()
