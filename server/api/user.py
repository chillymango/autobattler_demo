"""
Cache player credentials and information and what not locally.
"""
import os
from pydantic import BaseModel
from pydantic import Field
from utils.strings import uuid_as_str

DEFAULT_PATH = "current_player.json"


class NoCachedUser(ValueError):
    """
    Throw this if a user entity could not be loaded from cache
    """


class User(BaseModel):
    """
    (Human) User Abstraction
    """

    name: str
    id: str = Field(default_factory=uuid_as_str)

    @classmethod
    def from_cache(cls, path=DEFAULT_PATH):
        if not os.path.exists(path):
            raise NoCachedUser("Could not load a player from cache")
        return super().parse_file(path)

    def to_cache(self, path=DEFAULT_PATH):
        with open(path, 'w+') as output:
            output.write(self.json())
