from __future__ import annotations
import typing as T
from collections import namedtuple
from enum import Enum
from pydantic import BaseModel, Field, PrivateAttr

from engine.models.base import Entity
from engine.models.enums import Move
from engine.models.enums import PokemonId
from engine.models.enums import PokemonType
from engine.models.stats import Stats
from engine.utils.gamemaster import gamemaster
from utils.strings import uuid_as_str

if T.TYPE_CHECKING:
    pass

EvolutionConfig = namedtuple("EvolutionConfig", ["evolved_form", "turns_to_evolve"])

SHINY_STAT_MULT = 1.25
DEFAULT_XP_GAIN = 50.0


class BattleCard(BaseModel):
    """
    Pokemon Combat Representation

    Each Pokemon should have this instantiated
    """

    _id: str = PrivateAttr(default_factory=uuid_as_str)

    name: PokemonId
    move_f: Move
    move_ch: Move
    move_tm: Move
    _move_f_damage: T.Optional[float] = PrivateAttr(default=None)
    _move_ch_damage: T.Optional[float] = PrivateAttr(default=None)
    _move_tm_damage: T.Optional[float] = PrivateAttr(default=None)
    _move_f_energy: T.Optional[float] = PrivateAttr(default=None)
    _move_ch_energy: T.Optional[float] = PrivateAttr(default=None)
    _move_tm_energy: T.Optional[float] = PrivateAttr(default=None)
    level: float
    atk_: T.Optional[float] = None
    def_: T.Optional[float] = None
    health: T.Optional[float] = None
    _max_health: T.Optional[float] = PrivateAttr(default=0)
    f_move_spd: T.Optional[float] = None
    poke_type1: PokemonType = None
    poke_type2: PokemonType = None
    f_move_type: PokemonType = None
    ch_move_type: PokemonType = None
    tm_move_type: PokemonType = None
    tm_flag: bool = False
    shiny: bool = False
    energy: float = 0
    bonus_shield: int = 0
    status: int = 1
    choiced: bool = False
    team_position: int = None
    _item: "CombatItem" = PrivateAttr()

    # this tracks a current battle card modifier array
    # effective stats should be calcualated with these modifiers included
    modifiers: T.List[float] = Field(default_factory=lambda: [0] * 5)

    def reset_modifiers(self):
        self.modifiers = [0] * len(Stats)

    @property
    def attack(self):
        return self.atk_ + self.modifiers[Stats.ATK.value]

    @property
    def defense(self):
        return self.def_ + self.modifiers[Stats.DEF.value]

    @property
    def hitpoints(self):
        return self.health + self.modifiers[Stats.HP.value]

    @property
    def speed(self):
        return self.modifiers[Stats.SPD.value]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # stats
        poke_stats = gamemaster.get_default_pokemon_stats(self.name)
        cpms = gamemaster.get_lvl_cpm(self.level)
        self.health = kwargs.get('health') or cpms * poke_stats["baseStats"]["hp"]
        self._max_health = self.health
        self.atk_ = kwargs.get('atk_') or cpms * poke_stats["baseStats"]["atk"]
        self.def_ = kwargs.get('def_') or cpms * poke_stats["baseStats"]["def"]

        # types
        if not self.poke_type1:
            self.poke_type1 = PokemonType[poke_stats["types"][0].lower()]
        self.poke_type2 = kwargs.get('poke_type2') or PokemonType[poke_stats["types"][1].lower()]
        if not self.poke_type2 or self.poke_type2 == PokemonType.none:
            self.poke_type2 = self.poke_type1

        # moves
        move_f_stats = gamemaster.get_default_move_stats(self.move_f)
        self._move_f_damage = kwargs.get('_move_f_damage') or move_f_stats["power"]
        self.f_move_spd = kwargs.get('speed') or move_f_stats["cooldown"]
        self._move_f_energy = kwargs.get('_move_f_energy') or move_f_stats['energyGain']
        move_ch_stats = gamemaster.get_default_move_stats(self.move_ch)
        self._move_ch_damage = kwargs.get('_move_ch_damage') or move_ch_stats["power"]
        move_tm_stats = gamemaster.get_default_move_stats(self.move_tm)
        self._move_ch_energy = kwargs.get('_move_ch_energy') or move_ch_stats['energy']
        if move_tm_stats is not None:
            self._move_tm_damage = kwargs.get('_move_tm_damage') or move_tm_stats["power"]
            self.tm_move_type = kwargs.get('tm_move_type') or move_tm_stats["type"]
            self._move_tm_energy = kwargs.get("_move_tm_energy") or move_tm_stats["energy"]
        else:
            self._move_tm_damage = 0
            self.tm_move_type = PokemonType.none
            self._move_tm_energy = 0

        # move types
        self.f_move_type = kwargs.get('f_move_type') or move_f_stats["type"]
        self.ch_move_type = kwargs.get('ch_move_type') or move_ch_stats["type"]

    def __hash__(self):
        return hash(self._id)

    @property
    def max_health(self) -> float:
        return self._max_health

    @property
    def atk_spd_timer_cts(self) -> float:
        """
        Returns the number of timer counts required before a fast attack can be initiated.

        This depends on the base speed and the spd_ modifier.

        Since the game engine ticks at 100 timer counts a tick, the soft cap on effective attack
        speed is 10 attacks per second. That limit is enforced here.
        """
        return max(self.f_move_spd - self.speed * 50, 100.0)

    def atk_per_sec_for_spd_stat(self, spd: int):
        """
        Given some speed stat, calculate atk / sec
        """
        return 1000.0 / max(self.f_move_spd - spd * 50.0, 100.0)

    @property
    def atk_per_sec(self) -> float:
        """
        Returns the number of fast attacks this Pokemon will perform in one second.

        One second is 1000 timer counts.
        """
        return 1000.0 / self.atk_spd_timer_cts

    @property
    def item(self):
        return self._item

    def give_item(self, item: "CombatItem"):
        self._item = item

    def make_shiny(self):
        """
        Mark a Pokemon as shiny and adjust stats.

        Does nothing if the Pokemon is already shiny.
        """
        if self.shiny:
            return False
        self.shiny = True
        self.atk_ *= SHINY_STAT_MULT
        self.def_ *= SHINY_STAT_MULT
        self.health *= SHINY_STAT_MULT

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
        name = PokemonId[l[0]]
        move_f = Move[l[1]]
        move_ch = Move[l[2]]
        move_tm = Move[l[3]]
        return BattleCard(
            name = name,
            move_f = move_f,
            move_ch = move_ch,
            move_tm = move_tm,
            level = l[4],
            a_iv = l[5], 
            d_iv = l[6], 
            hp_iv = l[7],
            tm_flag = 0,
            shiny = 0
        )

    def __repr__(self):
        return "BattleCard({}): {}".format(self.name, self.to_string())


class Pokemon(Entity):
    """
    Instantiate unique object based on name
    """

    name: PokemonId
    battle_card: BattleCard
    nickname: str
    xp: float = 0.0

    def __str__(self):
        return ("Shiny" * self.battle_card.shiny + " {}".format(self.nickname)).strip()

    def __repr__(self):
        return "{} ({})".format(self.name, self.id)

    def __eq__(self, other):
        try:
            return self.id == getattr(other, 'id')
        except AttributeError:
            return False

    def is_type(self, poketype: str):
        """
        Check if a Pokemon is of a type

        References the battle card
        """
        return poketype in (self.battle_card.poke_type1, self.battle_card.poke_type2)

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
        print("adding xp")
        self.xp += amount


from engine.models.items import CombatItem
BattleCard.update_forward_refs()
Pokemon.update_forward_refs()
