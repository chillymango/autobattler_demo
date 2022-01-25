"""
I hate this so much
"""
import json
import weakref
import typing as T
from collections import defaultdict
from pydantic import BaseModel, Field
from pydantic import PrivateAttr

from engine.models.base import Entity


OO_ASSOCIATION_REGISTRY = defaultdict(lambda: {})  # lookup of Association by model / instance
OM_ASSOCIATION_REGISTRY = defaultdict(  # lookup of Association by model / instance
    lambda: defaultdict(lambda: [])
)
MM_ASSOCIATION_REGISTRY = NotImplemented

# maintain lookup of object to all associations
ENTITY_TO_ASSOCIATIONS: T.Dict[Entity, T.Dict[T.Type["Association"], T.List["Association"]]] = (
    defaultdict(lambda: defaultdict(lambda: []))
)


class Association(BaseModel):

    __slots__ = ['__weakref__']

    _ASSOCIATION_REGISTRY = PrivateAttr(default=NotImplemented)
    _LOOKUP_REGISTRY = PrivateAttr(default=NotImplemented)

    entity1: T.Any  # TODO: type annotate
    entity2: T.Any  # TODO: type annotate

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._register_self()

    def __del__(self):
        self.unregister_self()
        print(f'{self} is gone')

    def __hash__(self):
        """
        Associations are directionless
        """
        return hash(self.entity1 + self.entity2)

    def _register_self(self):
        """
        Check for uniqueness / add to registry.

        If this already exists, complain.
        """
        if self in self._ASSOCIATION_REGISTRY[self.__class__].values():
            raise ValueError(
                f"Association between {self.entity1} and {self.entity2} already exists"
            )
        self._ASSOCIATION_REGISTRY[self.__class__][self.entity1] = weakref.proxy(self)
        self._ASSOCIATION_REGISTRY[self.__class__][self.entity2] = weakref.proxy(self)

        self._LOOKUP_REGISTRY[self.entity1][self.__class__].append(weakref.proxy(self))
        self._LOOKUP_REGISTRY[self.entity2][self.__class__].append(weakref.proxy(self))

    def unregister_self(self):
        if self not in self._ASSOCIATION_REGISTRY[self.__class__].values():
            raise ValueError(
                f"Association between {self.entity1} and {self.entity2} does not exist"
            )
        import IPython; IPython.embed()
        self._ASSOCIATION_REGISTRY[self.__class__].pop(self.entity1)
        self._ASSOCIATION_REGISTRY[self.__class__].pop(self.entity2)

        self._LOOKUP_REGISTRY[self.entity1][self.__class__].remove(self)
        self._LOOKUP_REGISTRY[self.entity2][self.__class__].remove(self)


class OOAssociation(Association):
    """
    Represents a foreign key or something I guess
    """

    _ASSOCIATION_REGISTRY = PrivateAttr(default_factory=lambda: OO_ASSOCIATION_REGISTRY)
    _LOOKUP_REGISTRY = PrivateAttr(default_factory=lambda: ENTITY_TO_ASSOCIATIONS)


class OMAssociation(Association):
    """
    One-to-Many Association
    """

    _ASSOCIATION_REGISTRY = PrivateAttr(default_factory=lambda: OM_ASSOCIATION_REGISTRY)
    _LOOKUP_REGISTRY = PrivateAttr(default_factory=lambda: ENTITY_TO_ASSOCIATIONS)


class PokemonItemAssociation(OOAssociation):
    """
    Pokemon can hold a single item
    """


class PlayerInventoryAssociation(OMAssociation):
    """
    Players hold items in inventory
    """


class PlayerPartyAssociation(OMAssociation):
    """
    Players hold Pokemon in party
    """


class PlayerTeamAssociation(OMAssociation):
    """
    Players hold Pokemon in team
    """


class PlayerStorageAssociation(OMAssociation):
    """
    Players hold Pokemon in storage
    """


def get_associations_for_entity(entity: Entity) -> T.List[Association]:
    output: T.List[Association] = []

    registry = entity._ASSOCIATION_REGISTRY
    for obj, association in registry.items():
        if obj == entity:
            output.append(association)
    return output


class AssociatedContainer(BaseModel):
    """
    Container behavior should be defined as part of a mixin?
    """

    #__slots__ = ['__weakref__']

    _association_class: T.Type[Association] = PrivateAttr(default=None)
    _container_class: T.Type = PrivateAttr(default=list)
    _container_instance: T.Any = PrivateAttr(default=None)
    # NOTE: this is required because setting reference_entity Type to Entity will
    # cast the reference_entity into a Entity object instead of keeping the
    # original object. Unfortunate...
    reference_entity: T.Any
    container: T.Any

    def __init__(self, association_class: T.Type, container_class: T.Type = None, **kwargs):
        super().__init__(**kwargs)
        self._association_class = association_class
        self._container_class = container_class

    @property
    def container(self):
        """
        This is evaluated every time it is read
        """
        associations = ENTITY_TO_ASSOCIATIONS[self.reference_entity]
        container: T.List = []
        for assn in associations[self._association_class]:
            assn: Association
            if assn.entity1 == self.reference_entity:
                container.append(assn.entity2)
            elif assn.entity2 == self.reference_entity:
                container.append(assn.entity1)
            else:
                raise ValueError("This shouldn't be here")
        if self._container_class == list:
            run = self.modify_list_in_place
        elif self._container_class == set:
            run = self.modify_set_in_place
        else:
            raise ValueError(f"Container type {self._container_class} is not supported")

        if self._container_instance is None:
            self._container_instance = self._container_class(container)
        else:
            run(self._container_instance, self._container_class(container))

        return self._container_instance

    def modify_list_in_place(self, orig: T.List, required: T.List):
        """
        Modify the sequence in place so the reference doesn't break
        """
        orig[:] = required

    def modify_set_in_place(self, orig: T.Set, required: T.Set):
        orig.intersection_update(required)
        orig.update(required)

    def remove_association_from_container(self, association: Association):
        """
        Remove an association from the container
        """
        association.unregister_self()
