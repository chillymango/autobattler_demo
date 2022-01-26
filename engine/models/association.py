"""
Association Models
"""
from tkinter import E
import typing as T
from collections import defaultdict

from engine.models.base import Entity
from engine.models.base import Queryable
from engine.models.player import Player
from engine.models.items import Item
from engine.models.pokemon import Pokemon


class CompositePK(Queryable):
    """
    Composite primary key base
    """

    entity1: Entity
    entity2: Entity

    def __hash__(self):
        """
        Assumes entity1 and entity2 are unique...
        """
        return hash(self.entity1) + hash(self.entity2)


class OOAssociation(CompositePK):
    """
    A one-to-one association
    """


class OMAssociation(CompositePK):
    """
    A one-to-many association
    """


class PlayerShop(OMAssociation):
    """
    Associates players to their shops
    """
    entity1: Player  # one
    entity2: str  # many

    @classmethod
    def get_shop(cls, player: Player) -> T.List[str]:
        """
        Convenience method

        Returns a list of shop cards (strings) of Pokemon for a player
        """
        return [x.entity2 for x in cls.all(entity1=player)]


class PlayerInventory(OMAssociation):
    """
    Associates players to their inventory
    """

    entity1: Player  # one
    entity2: Item  # many

    @classmethod
    def get_inventory(cls, player: Player) -> T.List[Item]:
        """
        Convenience method

        Returns a list of items in an inventory for a player
        """
        return [x.entity2 for x in cls.all(entity1=player)]


class PlayerRoster(OMAssociation):
    """
    Associates players to their roster
    """

    entity1: Player
    entity2: Pokemon

    @classmethod
    def get_roster(cls, player: Player) -> T.List[Pokemon]:
        """
        Convenience method

        Returns a list of Pokemon in a roster for a player
        """
        return [x.entity2 for x in cls.all(entity1=player)]


class PokemonHeldItem(OOAssociation):
    """
    Associates Pokemon to their held item
    """

    entity1: Pokemon
    entity2: Item

    @classmethod
    def get_held_item(cls, pokemon: Pokemon) -> T.Optional[Item]:
        """
        Get the held item. Returns None if there is no Item.
        """
        items = [x.entity2 for x in cls.all(entity1=pokemon)]
        if items:
            return items[0]
        return None

    @classmethod
    def get_item_holder(cls, item: Item) -> T.Optional[Pokemon]:
        """
        Get the item holder. Returns None if there is no Item holder (???)
        """
        holders = [x.entity1 for x in cls.all(entity2=item)]
        if holders:
            return holders[0]
        return None


AssociationType = T.Union[T.Type[OOAssociation], T.Type[OMAssociation]]
Association = T.Union[OOAssociation, OMAssociation]
ASSOCIATIONS: T.Dict[AssociationType, Association] = defaultdict(lambda: set())


def associate(klass: AssociationType, entity1: Entity, entity2: Entity):
    """
    Associate two entities
    """
    assn = klass(entity1=entity1, entity2=entity2)
    ASSOCIATIONS[klass].add(assn)
    return assn


def dissociate(klass: AssociationType, entity1: Entity, entity2: Entity):
    """
    Dissociate two entities if they are associated
    """
    for assn in ASSOCIATIONS[klass]:
        if assn.entity1 == entity1 and assn.entity2 == entity2:
            ASSOCIATIONS[klass].remove(assn)
            break
