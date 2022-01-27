"""
Association Models
"""
import typing as T
from collections import defaultdict

from pydantic import PrivateAttr

from engine.models.base import Entity
from engine.models.base import Queryable
from engine.models.player import Player
from engine.models.items import Item
from engine.models.pokemon import Pokemon
from engine.models.shop import ShopOffer


class CompositePK(Queryable):
    """
    Composite primary key base
    """

    entity1: str
    entity2: str

    # hold references to objects to prevent them from being garbage collected
    _entity1: Entity = PrivateAttr()
    _entity2: Entity = PrivateAttr()

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
    entity1: str  #Player  # one
    entity2: str  #ShopOffer  # many

    @classmethod
    def get_shop(cls, player: Player) -> T.List[str]:
        """
        Convenience method

        Returns a list of shop cards (strings) of Pokemon for a player
        """
        return [ShopOffer.get_by_id(x.entity2) if x else None for x in cls.all(entity1=player.id)]


class PlayerInventory(OMAssociation):
    """
    Associates players to their inventory
    """
    entity1: str  #Player  # one
    entity2: str  #Item  # many

    @classmethod
    def get_inventory(cls, player: Player) -> T.List[Item]:
        """
        Convenience method

        Returns a list of items in an inventory for a player
        """
        return [Item.get_by_id(x.entity2) for x in cls.all(entity1=player.id)]


class PlayerRoster(OMAssociation):
    """
    Associates players to their roster
    """

    @classmethod
    def get_roster(cls, player: Player) -> T.List[Pokemon]:
        """
        Convenience method

        Returns a list of Pokemon in a roster for a player
        """
        return [Pokemon.get_by_id(x.entity2) for x in cls.all(entity1=player.id)]


class PokemonHeldItem(OOAssociation):
    """
    Associates Pokemon to their held item
    """

    @classmethod
    def get_held_item(cls, pokemon: Pokemon) -> T.Optional[Item]:
        """
        Get the held item. Returns None if there is no Item.
        """
        items = [Item.get_by_id(x.entity2) for x in cls.all(entity1=pokemon)]
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
    assn = klass(entity1=entity1.id, entity2=entity2.id)
    assn._entity1 = entity1
    assn._entity2 = entity2
    ASSOCIATIONS[klass].add(assn)
    return assn


def dissociate(klass: AssociationType, entity1: Entity, entity2: Entity):
    """
    Dissociate two entities if they are associated
    """
    for assn in ASSOCIATIONS[klass]:
        if assn.entity1 == entity1.id and assn.entity2 == entity2.id:
            assn._entity1 = None
            assn._entity2 = None
            ASSOCIATIONS[klass].remove(assn)
            assn.delete()
            break
    else:
        raise Exception(f'{entity1} and {entity2} are not associated by {klass}')
