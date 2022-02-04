import copy
import json
import typing as T
import weakref
from uuid import UUID

from pydantic import BaseModel, PrivateAttr
from pydantic import Field
from pydantic.main import ModelMetaclass
from utils.strings import uuid_as_str


class queryable_meta(ModelMetaclass):

    def __new__(cls, name, parents, attrs):
        attrs['_INSTANCES'] = dict()
        _cls = super().__new__(cls, name, parents, attrs)
        return _cls


_Entity = T.TypeVar("Entity")

class Queryable(BaseModel, metaclass=queryable_meta):
    """
    Generic queryable object.

    Should be searchable with a weakref to itself being recorded as a class attribute.

    TODO: namespace this by env.Environment so all entities associated with an env can be
    collected and destroyed when a game ends. This is causing significant pollution...
    """
    __slots__ = ['__weakref__']

    def __gt__(self, other):
        return int(UUID(other.id)) > int(UUID(self.id))

    def __ge__(self, other):
        return int(UUID(other.id)) >= int(UUID(self.id))

    def __lt__(self, other):
        return int(UUID(other.id)) < int(UUID(self.id))

    def __le__(self, other):
        return int(UUID(other.id)) <= int(UUID(self.id))

    def __hash__(self):
        return hash(self.id)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self._INSTANCES.get(hash(self)) is not None:
            self = self._INSTANCES[hash(self)]()
            return
        self._INSTANCES[hash(self)] = weakref.ref(self)

    # NOTE: i think we're opting for manual garbage collection with `delete` being
    # called explicitly instead of implicitly assuming the object should be deleted
    # if an instance has no refcounts left. The Python object and the Entity are not
    # the same thing, and so there should be no __del__ method.

    # expose some SQLAlchemy-like interfaces
    # TODO: i'm sure i can figure out how to mimic that smooth interface...
    # the `generative` decorator is probably the way to go
    @classmethod
    def query(cls, **params) -> T.Iterator[_Entity]:
        """
        Query all instances for parameter match. The parameter match acts as a strong filter,
        so if multiple parameter inputs are provided, only the instances that match all of them
        will be returned.
        """
        # TODO: making a copy is expensive, shouldn't do it...
        # not using the original list is important to allow the iterator to modify the instances
        # list without throwing an Exception
        entities = copy.copy(cls._INSTANCES)
        # search self first
        for entity in entities.values():
            for param, value in params.items():
                if getattr(entity(), param) != value:
                    break
            else:
                yield entity()

        # search children after
        for child in cls.__subclasses__():
            for item in child.query(**params):
                yield item

    @classmethod
    def get_by_id(cls, id: str) -> _Entity:
        """
        Return an exact match by ID
        """
        if id is None:
            raise ValueError("Cannot hash NoneType")

        if hash(id) in cls._INSTANCES:
            return cls._INSTANCES.get(hash(id))()

        # if we cannot find it immediately, check subclasses
        for child in cls.__subclasses__():
            child_search = child.get_by_id(id)
            if child_search is not None:
                return child.get_by_id(id)
        # return None if there is no match at all
        return None

    @classmethod
    def all(cls, **params) -> T.List[_Entity]:
        """
        Return all matches with params
        """
        return list(cls.query(**params))

    def delete(self):
        """
        Delete this object

        Remove references to this object from instance registry
        """
        try:
            self.__class__._INSTANCES.pop(hash(self))
        except KeyError:
            # already deleted
            print('Object already deleted??')
            pass


class Entity(Queryable):
    """
    Unique object (carries an ID)
    """

    id: str = Field(default_factory=uuid_as_str)
