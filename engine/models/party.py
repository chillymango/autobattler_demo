"""
Pokemon Party, Team, and Storage Configuration

Details how to split a roster into partm, team, and storage.

The UI will manipulate this information and send updates back to the server.

Gawd Bless WebSockets
"""
import typing as T
from pydantic import BaseModel
from pydantic import validator

MAX_PARTY_SIZE = 6


class PartyConfig(BaseModel):
    """
    The storage is implicit (not in party = in storage)
    """

    party: T.List[T.Optional[str]] = [] # list of Pokemon IDs
    team: T.List[str] = [] # list of Pokemon IDs

    @validator('party')
    def validate_party(cls, value: T.List[str]):
        """
        Verify that the party never exceeds size of 6.
        """
        if len(value) > 6:
            raise ValueError("Party size cannot exceed 6")
        return value

    @validator('team')
    def validate_team(cls, value: T.List[str]):
        """
        Verify that team size never exceeds 3
        """
        if len(value) > 3:
            raise ValueError("Team size cannot exceed 3")
        return value

    @property
    def party_is_full(self):
        return sum([1 if x is not None else 0 for x in self.party]) == 6

    @property
    def team_is_full(self):
        return sum([1 if x is not None else 0 for x in self.team]) == 3

    def add_to_party(self, poke_id: str, idx: int = None) -> bool:
        """
        Add Pokemon to party (by ID).

        If an index is provided, the Pokemon value will be written in directly.
        Any existing Pokemon that may have been there will be moved to storage.
        If an index is not provided, the Pokemon will be written into the first
        empty value.
        """
        if self.party_is_full:
            return False

        if poke_id in self.party:
            return False

        if idx is None:
            # find first empty slot
            for idx, slot in enumerate(self.party):
                if slot is None:
                    self.party[idx] = poke_id
                    return True
            else:
                if len(self.party) < 6:
                    self.party.append(poke_id)
                    return True
            return False

        self.party[idx] = poke_id
        return True

    def populate_team_from_party(self):
        """
        If the team is not full, pull party members from team until there are either
        no party members left to pull, or the team is full.
        """
        idx = 0
        while not self.team_is_full and idx < len(self.party):
            self.add_to_team_by_idx(idx)
            idx += 1

    def remove_from_party_by_idx(self, idx: int):
        """
        Remove Pokemon from party by index
        """
        self.party[idx] = None

    def remove_from_party(self, poke_id: str):
        """
        Remove Pokemon from party

        If the Pokemon is not in the party, do nothing.
        """
        for idx, party_poke_id in enumerate(self.party):
            if party_poke_id == poke_id:
                self.remove_from_party_by_idx(idx)

    def add_to_team(self, poke_id: str) -> bool:
        """
        Add Pokemon to team (by ID).

        Will always add to the first free team slot.
        """
        if self.team_is_full:
            return False
        self.team.append(poke_id)
        return True

    def add_to_team_by_idx(self, idx: int) -> bool:
        """
        Add Pokemon to team (by idx)

        Will always add to the first free team slot
        """
        return self.add_to_team(self.party[idx])

    def remove_from_team_by_idx(self, idx: int):
        """
        Remove from team by index
        """
        self.team.remove(self.team[idx])

    def remove_from_team(self, poke_id: str):
        """
        Remove Pokemon from team (by ID).

        If the Pokemon is not on the team, do nothing.
        """
        for idx, team_poke_id in enumerate(self.team):
            if team_poke_id == poke_id:
                self.remove_from_team_by_id(idx)

    def shift_team_up(self, idx: int):
        """
        Swap the position of a team member with the one above it.

        If the Pokemon is already at the top, do nothing.
        """
        if idx < 1:
            return
        self.team[idx - 1], self.team[idx] = self.team[idx], self.team[idx - 1]

    def shift_team_down(self, idx: int):
        """
        Swap the position of a team member with the one below it.

        If the Pokemon is already at the bottom, do nothing.
        """
        if idx >= len(self.team) - 1:
            return
        self.team[idx], self.team[idx + 1] = self.team[idx + 1], self.team[idx]
