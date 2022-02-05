"""
Hero Models
"""
import typing as T
from enum import Enum
from pydantic import BaseModel

from engine.models.items import PlayerHeroPower
from engine.models.items import *

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
    _power: T.Type[HeroPowerType] = PrivateAttr(default=None)
    _env: "Environment" = PrivateAttr(default=None)
    showdown_avatar: str

    def __init__(self, _env=None, _power=None, **kwargs):
        super().__init__(**kwargs)
        if _power is not None:
            self._power = _power(_env=_env)
        else:
            self._power = None

    def set_env(self, _env: "Environment"):
        if self._power is None:
            return
        self._power._env = _env

    class Config:
        fields = {
            "power": {
                "exclude": "*"
            }
        }


NORMAL_HEROES: T.List[Hero] = [
    Hero(name="Brock", ability_name="Brock Solid", _power=BrockShieldPower, showdown_avatar = "brock"),
    Hero(name="Blaine", ability_name="PUSH THE BUTTON", _power=BlaineButton, showdown_avatar = "blaine"),
    Hero(name="Blue", ability_name = "Smell 'ya Later", _power=BlueSmell, showdown_avatar = "blue"),
    Hero(name="Bruno", ability_name="Thicc Bod", _power=BrunoBod, showdown_avatar = "bruno"),
    Hero(name="Erika", ability_name="Herb Master", _power=ErikaGarden, showdown_avatar = 'erika'),
    Hero(name="Giovanni", ability_name="Crypto Dividends", _power=GiovanniGains, showdown_avatar = 'giovanni'),
    Hero(name='Green', ability_name='Mineral Collector', _power = GreensRocks, showdown_avatar = "leaf-gen3"),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution', _power = KogaNinja, showdown_avatar ="janine"),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning', _power = JanineJutsu, showdown_avatar = "koga"),
    Hero(name='Lance', ability_name='"Dragon" Master', _power = LanceFetish, showdown_avatar = "lance"),
    Hero(name='Lt. Surge', ability_name='Gorilla Warfare', _power = SurgeGorilla, showdown_avatar = 'ltsurge'),
    Hero(name='Misty', ability_name='Trust Fund', _power = MistyTrustFund, showdown_avatar = "misty"),
    Hero(name='Red', ability_name='Plot Armor', _power = RedCheater, showdown_avatar = 'red'),
    Hero(name='Jessie and James', ability_name='Blast Off!!', _power = BlastOff, showdown_avatar = 'teamrocket'),
    Hero(name='Sabrina', ability_name='Clairvoyance', _power = SabrinaFuture, showdown_avatar = 'sabrina'), 
    Hero(name='Will', ability_name='Chunnibyou', _power = WillSac, showdown_avatar = 'will'),
]

PRISMATIC_HEROES = [x for x in NORMAL_HEROES]
#PRISMATIC_HEROES: T.List[Hero] = [
#    # TODO: fill out
#    Hero(name="Brock", ability_name="Rock Solid", _power=None),
#    Hero(name="Blaine", ability_name="Blaze It", _power=None),
#    Hero(name="Blue", ability_name = "Smell 'ya Later", _power=None),
#    Hero(name="Bruno", ability_name="Thicc Bod", _power=None),
#    Hero(name="Erika", ability_name="Herb Master", _power=None),
#    Hero(name="Giovanni", ability_name="Crypto Dividends", _power=None),
#    Hero(name='Green', ability_name='Mineral Collector'),
#    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution'),
#    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning'),
#    Hero(name='Lance', ability_name='"Dragon" Master')
#]

HERO_CONTEXT: T.Dict[Hero, str] = {}
