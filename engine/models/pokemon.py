import typing as T
from collections import namedtuple
from pydantic import BaseModel
from pydantic import Field
from uuid import UUID

from utils.strings import uuid_as_str

EvolutionConfig = namedtuple("EvolutionConfig", ["evolved_form", "turns_to_evolve"])

DEFAULT_XP_GAIN = 50.0


class BattleCard(BaseModel):
    """
    Pokemon Combat Representation

    Each Pokemon should have this instantiated
    """

    name: str
    move_f: str
    move_ch: str
    move_tm: str
    level: float
    a_iv: int
    d_iv: int
    hp_iv: int
    poke_type1: str = None
    poke_type2: str = None
    f_move_type: str = None
    ch_move_type: str = None
    tm_move_type: str = None
    tm_flag: bool = False
    shiny: bool = False
    health: int = 0
    energy: int = 0
    bonus_shield: int = 0
    status: int = 1
    choiced: bool = False
    team_position: int = None
    berry: str = None

    def make_shiny(self):
        """
        Mark a Pokemon as shiny and adjust stats.

        Does nothing if the Pokemon is already shiny.
        """
        if self.shiny:
            return False
        self.shiny = True
        return True

    def set_tm_move(self, move):
        """
        Add a TM move to a Pokemon

        Does nothing if the Pokemon already has a TM move.
        """
        if self.tm_flag:
            return False
        self.tm_flag = True
        self.move_tm = move.lower()
        return True

    @classmethod
    def from_string(cls, string):
        """
        Parse from a comma-delimited string

        This will initialize as a default.
        """
        l = string.split(',')
        return BattleCard(
            name = l[0],
            move_f = l[1],
            move_ch = l[2],
            move_tm = l[3],
            level = l[4],
            a_iv = l[5], 
            d_iv = l[6], 
            hp_iv = l[7],
            tm_flag = 0,
            shiny = 0
        )

    def to_string(self):
        """
        Return a PvPoke string representation of the Pokemon
        """
        return ",".join(str(x) for x in [
            self.name,
            self.move_f,
            self.move_ch,
            self.move_tm,
            self.level,
            self.a_iv,
            self.d_iv,
            self.hp_iv,
        ])

    def __repr__(self):
        return "BattleCard({}): {}".format(self.name, self.to_string())


class Pokemon(BaseModel):
    """
    Instantiate unique object based on name
    """

    name: str
    battle_card: BattleCard
    nickname: str
    id: str = Field(default_factory=uuid_as_str)
    xp: float = 0.0

    def __hash__(self):
        try:
            return int(UUID(self.id))
        except Exception:
            print(self.name)
            print(self.id)
            raise

    def __str__(self):
        return ("Shiny" * self.battle_card.shiny + " {}".format(self.nickname)).strip()

    def __repr__(self):
        return "{} ({})".format(self.name, self.id)

    def __eq__(self, other):
        try:
            return self.id == getattr(other, 'id')
        except AttributeError:
            return False

    @classmethod
    def from_dict(cls, data):
        pokemon = cls(
            pokemon_name=data['name'],
            battle_card=BattleCard.from_dict(data['battle_card']),
            nickname=data['nickname'],
            id=data['id']
        )
        pokemon.xp = data['xp']
        return pokemon

    def add_xp(self, amount=DEFAULT_XP_GAIN):
        """
        Add experience to a Pokemon
        """
        self.xp += amount
