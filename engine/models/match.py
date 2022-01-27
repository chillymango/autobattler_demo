import typing as T
from pydantic import BaseModel

from engine.models.player import Player


class Match(BaseModel):
    """
    Represents a match between two players.
    """

    player1: str
    player2: str
    result: T.Union[Player, None] = None

    @property
    def players(self):
        return (self.player1, self.player2)

    def has_player(self, player_id):
        return player_id in self.players

    def __hash__(self):
        return hash((self.player1, self.player2))
