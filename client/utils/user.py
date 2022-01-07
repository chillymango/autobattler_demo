"""
Cache player credentials and information and what not locally.
"""
import json
import os
from uuid import uuid4

DEFAULT_PATH = "current_player.json"


class NoCachedUser(ValueError):
    """
    Throw this if a user entity could not be loaded from cache
    """


class User:
    """
    (Human) User Abstraction
    """

    def __init__(self, first, last, id=None):
        self.first = first.strip()
        self.last = last.strip()
        self.id = id or uuid4()

    @property
    def name(self):
        return '{} {}'.format(self.first, self.last)

    @classmethod
    def from_cache(cls, path=DEFAULT_PATH):
        if not os.path.exists(path):
            raise NoCachedUser("Could not load a player from cache")
        with open(path, 'r') as jsonfile:
            try:
                content = json.load(jsonfile)
            except ValueError as exc:
                raise NoCachedUser(exc)

        return cls(content['first'], content['last'], content['id'])

    def to_cache(self, path=DEFAULT_PATH):
        """
        Write player contents to cache
        """
        output = dict(
            first=self.first, last=self.last, id=str(self.id)
        )
        with open(path, 'w+') as jsonfile:
            json.dump(output, jsonfile)
