"""
Player Representation
"""
import typing as T
from pydantic import BaseModel

if T.TYPE_CHECKING:
    from engine.player import Player as PlayerObject


class Player(BaseModel):
    id: str
    name: str

    @classmethod
    def from_player_object(cls, player_object: "PlayerObject"):
        return cls(name=player_object.name, id=str(player_object.id))
