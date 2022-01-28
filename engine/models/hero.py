"""
Hero Models
"""
import typing as T
from enum import Enum
from pydantic import BaseModel

from engine.models.items import PlayerHeroPower


class HeroGrade(Enum):
    # TODO: rename so no sue by rito
    SILVER = 0
    GOLD = 1
    PRISMATIC = 2


class Hero(BaseModel):
    """
    Heroes are special powers a player has.

    Hero function is encapsulated within the PlayerHeroPower class.
    """

    name: str
    grade: HeroGrade = HeroGrade.SILVER
    ability_name: str
    power: PlayerHeroPower = None  # TODO: make this not default


NORMAL_HEROES: T.List[Hero] = [
    Hero(name="Brock", ability_name="Rock Solid", power=None),
    Hero(name="Blaine", ability_name="Blaze It", power=None),
    Hero(name="Blue", ability_name = "10-Badge Trainer", power=None),
    Hero(name="Bruno", ability_name="Thicc Bod", power=None),
    Hero(name="Erika", ability_name="Herb Master", power=None),
    Hero(name="Giovanni", ability_name="Crypto Dividends", power=None),
    Hero(name='Green', ability_name='Mineral Collector'),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution'),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning'),
    Hero(name='Lance', ability_name='"Dragon" Master')
]

PRISMATIC_HEROES: T.List[Hero] = [
    # TODO: fill out
    Hero(name="Brock", ability_name="Rock Solid", power=None),
    Hero(name="Blaine", ability_name="Blaze It", power=None),
    Hero(name="Blue", ability_name = "10-Badge Trainer", power=None),
    Hero(name="Bruno", ability_name="Thicc Bod", power=None),
    Hero(name="Erika", ability_name="Herb Master", power=None),
    Hero(name="Giovanni", ability_name="Crypto Dividends", power=None),
    Hero(name='Green', ability_name='Mineral Collector'),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution'),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning'),
    Hero(name='Lance', ability_name='"Dragon" Master')
]

HERO_CONTEXT: T.Dict[Hero, str] = {}
