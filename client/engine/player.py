"""
Player Object Model
"""
from enum import Enum

from engine.base import Component

MAX_STORAGE_SIZE = 30
MAX_PARTY_SIZE = 6
TEAM_SIZE = 3


class EntityType(Enum):
    HUMAN = 0
    COMPUTER = 1
    CREEP = 2


class Player:
    """
    This probably needs to do something more complicated later
    """

    def __init__(self, name, type_=EntityType.COMPUTER):
        self.name = name
        self.type = type_
        self.is_alive = None

        self.inventory = {}  # maps item classes to counts of each item

        self.party = [None] * MAX_PARTY_SIZE
        self.storage = []
        self.team = []

        self.hitpoints = 0
        self.balls = 0  # pokeballs are used to catch pokemon from the wild
        self.energy = 0  # energy is used to 'roll' the shop

        # TODO: this sucks, do something smarter
        self.signals = []

        self.team_locked = False
        self.party_locked = False

    @property
    def party_is_full(self):
        return sum(member is not None for member in self.party) == MAX_PARTY_SIZE

    @property
    def team_is_full(self):
        return len(self.team) >= 3

    @property
    def roster(self):
        """
        Party + Storage

        Team is a subset of party. Party and storage are distinct containers.

        List order is always party pokemon first and then storage pokemon.
        """
        return [x for x in self.party if x is not None] + self.storage

    def add_to_party(self, pokemon):
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
        """
        self.storage.remove(self.storage[idx])

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
    def create_from_user(cls, user):
        """
        Users are always human
        """
        return cls(user.name, type_=EntityType.HUMAN)

    def __repr__(self):
        if self.is_alive:
            livestr = "Alive"
        elif self.is_alive is None:
            livestr = "Uninitialized"
        elif not self.is_alive:
            livestr = "Dead"

        return "{} Player: {} ({})".format(self.type.name.capitalize(), self.name, livestr)


class PlayerManager(Component):
    """
    Keeps track of players from turn to turn
    """

    def initialize(self):
        self.players = self.state.players
        for player in self.players:
            player.is_alive = True
            player.hitpoints = 20
            player.balls = 5

    def turn_setup(self):
        """
        Add balls, run special events before prep phase
        """
        # base update
        # TODO: make this scale as the game goes on
        for player in self.players:
            player.balls += 2
            player.energy += 5

    def turn_cleanup(self):
        """
        Check if any player has health at 0 or less. If so, mark them as dead.
        """
        for player in self.players:
            if player.hitpoints <= 0:
                player.is_alive = False
