import typing as T
from pydantic import BaseModel

from engine.models.player import Player


class Match(BaseModel):
    """
    Represents a match between two players.
    """

    player1: Player
    player2: Player
    result: T.Union[Player, None] = None

    @property
    def players(self):
        return (self.player1, self.player2)

    def has_player(self, player):
        return player in self.players

    def __hash__(self):
        return hash((self.player1, self.player2))

    @property
    def is_creep_match(self):
        return "Creep Round" in self.player1.name or "Creep Round" in self.player2.name

    def __repr__(self):
        if self.result:
            resultstr = "{} wins".format(self.result)
        else:
            resultstr = "Not played"
        return "Match - ({}) vs ({}) ({})".format(self.player1, self.player2, resultstr)
