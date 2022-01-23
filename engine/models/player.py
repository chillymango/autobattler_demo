from __future__ import annotations
import typing as T
from enum import Enum
from pydantic import BaseModel
from pydantic import Field
from uuid import UUID

from engine.models.items import Item
from engine.models.pokemon import Pokemon
from utils.strings import uuid_as_str

if T.TYPE_CHECKING:
    from server.api.user import User

MAX_STORAGE_SIZE = 30
MAX_PARTY_SIZE = 6
TEAM_SIZE = 3


class EntityType(Enum):
    HUMAN = 0
    COMPUTER = 1
    CREEP = 2


class Player(BaseModel):
    """
    This probably needs to do something more complicated later
    """

    name: str
    type: EntityType = EntityType.COMPUTER
    is_alive: bool = True
    inventory: T.Set[Item] = set()
    party: T.List[T.Union[Pokemon, None]] = [None] * 6
    storage: T.List[Pokemon] = []
    team: T.List[Pokemon] = []
    hitpoints: int = 0
    balls: int = 0
    energy: int = 0
    master_balls: int = 0
    flute_charges: int = 0
    id: str = Field(default_factory=uuid_as_str)
    party_locked: bool = False
    team_locked: bool = False

    def __hash__(self):
        """
        Use the objects id (uuid) as a hash
        """
        try:
            return int(UUID(self.id))
        except Exception:
            print(self.name)
            print(self.id)
            raise

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.name == other.name and self.type == other.type and self.id == other.id

    @property
    def is_creep(self):
        return self.type == EntityType.CREEP

    @property
    def party_is_full(self):
        return sum(member is not None for member in self.party) == MAX_PARTY_SIZE

    @property
    def team_is_full(self):
        return len(self.team) >= 3

    @property
    def storage_is_full(self):
        return len(self.storage) >= MAX_STORAGE_SIZE

    @property
    def roster(self):
        """
        Party + Storage

        Team is a subset of party. Party and storage are distinct containers.

        List order is always party pokemon first and then storage pokemon.
        """
        return [x for x in self.party if x is not None] + self.storage

    def add_to_party(self, pokemon: "Pokemon"):
        """
        Add Pokemon to first free party spot

        Returns True if successful and False if not.
        """
        if self.party_locked:
            return False

        if not self.party_is_full:
            for idx, member in enumerate(self.party):
                if member is None:
                    self.party[idx] = pokemon
                    return True

        return False

    def release_from_party(self, idx):
        """
        Release pokemon by index in party
        """
        if self.party[idx] in self.team:
            team_idx = self.team.index(self.party[idx])
            self.remove_from_team(team_idx)

        self.party[idx] = None

    def add_item(self, item):
        """
        add item to inventory
        """
        if item in self.inventory.keys():
            self.inventory[item] += 1 
        else:
            self.inventory[item] = 1

    def remove_item(self, item):
        """
        remove item from inventory
        """
        if item in self.inventory.keys():
            self.inventory[item] += -1 
        else:
            self.inventory[item] = 0

    def add_to_team(self, pokemon):
        """
        Add a Pokemon to the team.

        Pokemon needs to be a member of the party first.
        """
        if pokemon not in self.party:
            print('Pokemon {} needs to be in the party first'.format(pokemon))
            return
        idx = self.party.index(pokemon)
        self.add_party_to_team(idx)

    def add_party_to_team(self, idx):
        """
        Add a Pokemon from the party to the team.
        """
        if self.team_locked:
            return
        if self.team_is_full:
            return

        if self.party[idx] in self.team:
            print("Pokemon already in team")
            return

        self.team.append(self.party[idx])

    def remove_from_team(self, idx):
        """
        Remove a Pokemon from the team
        """
        if self.team_locked:
            return

        self.team.remove(self.team[idx])

    def add_to_storage(self, pokemon):
        """
        Add Pokemon to Storage
        """
        if len(self.storage) < MAX_STORAGE_SIZE:
            self.storage.append(pokemon)
            return True
        else:
            print('No room to add {} to team'.format(pokemon))

    def release_from_storage(self, idx):
        """
        Release pokemon by index in storage.

        If the Pokemon was holding items, put them in player inventory.
        """
        poke: Pokemon = self.storage[idx]
        # TODO: this is an example of a non-associative interaction being shitty
        if poke.battle_card.berry is not None:
            self.inventory.add(poke.battle_card.berry)
            poke.battle_card.berry = None
        self.storage.remove(self.storage[idx])

    def release_by_id(self, id):
        """
        search both storage and party for a specific poke and remove it
        """

        if len(self.storage) >0:
            for index, poke in enumerate(self.storage):
                if poke.id == id:
                    self.release_from_storage(index)
                    break
        for index, poke in enumerate(self.party):
            if poke is None:
                continue
            if poke.id == id:
                self.release_from_party(index)
                break

    def move_party_to_storage(self, pokemon):
        """
        Move Pokemon from party to storage

        Runs a check to ensure that the Pokemon is in party first and that
        storage is not full.
        """
        if pokemon is None:
            raise Exception(f'Null Pokemon submitted for move')
        if pokemon not in self.party:
            raise Exception(f"{pokemon} not in party")
        if self.add_to_storage(pokemon):
            self.release_from_party(self.party.index(pokemon))
            if pokemon in self.team:
                self.remove_from_team(self.team.index(pokemon))
        else:
            raise Exception("Player storage is full")

    def move_storage_to_party(self, pokemon):
        """
        Move Pokemon from storage to party
        """
        if pokemon not in self.storage:
            raise Exception(f'{pokemon} not in storage')
        if self.add_to_party(pokemon):
            self.release_from_storage(self.storage.index(pokemon))
        else:
            raise Exception("Failed to add Pokemon to party")

    def add_to_roster(self, pokemon):
        """
        Add Pokemon

        If the party is not yet filled, add Pokemon to party.

        If the party is filled, add Pokemon to storage.

        If storage is filled, get mad.
        """
        if not self.add_to_party(pokemon):
            if not self.add_to_storage(pokemon):
                print("No room to add to roster")
                return False
        return True

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
