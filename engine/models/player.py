from __future__ import annotations
import typing as T
from enum import Enum
from pydantic import Field

from engine.models.base import Entity
from engine.models.party import PartyConfig

if T.TYPE_CHECKING:
    from server.api.user import User

MAX_STORAGE_SIZE = 30
MAX_PARTY_SIZE = 6
TEAM_SIZE = 3


class EntityType(Enum):
    HUMAN = 0
    COMPUTER = 1
    CREEP = 2


class Player(Entity):
    """
    This probably needs to do something more complicated later
    """

    name: str
    type: EntityType = EntityType.COMPUTER
    is_alive: bool = True
    party_config: PartyConfig = Field(default_factory=PartyConfig)
    hitpoints: int = 0
    balls: int = 0
    energy: int = 0
    master_balls: int = 0
    flute_charges: int = 0
    party_locked: bool = False
    team_locked: bool = False

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.name == other.name and self.type == other.type and self.id == other.id

    @property
    def is_creep(self):
        return self.type == EntityType.CREEP

    def add_to_team_by_idx(self, party_idx: int):
        """
        Move a Pokemon into the team
        """
        self.party_config.add_to_team(self.party_config.party[party_idx])

    def remove_from_team_by_idx(self, team_idx: int):
        """
        Remove a Pokemon from a team
        """
        self.party_config.remove_from_team_by_idx(team_idx)

    def update_party_config(self, party_poke_id: str):
        """
        Update the party config

        If the party is not full, party members will be pulled from storage to fill.
        """
        self.party_config.add_to_party(party_poke_id)

    @classmethod
    def create_from_user(cls, user: "User"):
        """
        Users are always human
        """
        return cls(name=user.name, type=EntityType.HUMAN, id=user.id)

    def __str__(self):
        return self.name

    def __repr__(self):
        if self.is_alive:
            livestr = "Alive"
        elif self.is_alive is None:
            livestr = "Uninitialized"
        elif not self.is_alive:
            livestr = "Dead"

        if self.type == EntityType.CREEP:
            return "Creep Player"
        return "{} Player: {} ({})".format(self.type.name.capitalize(), self.name, livestr)


from engine.models.pokemon import Pokemon
Player.update_forward_refs()
