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
    Hero(name="Brock", ability_name="Rock Solid", _power=BrockShieldPower),
    Hero(name="Blaine", ability_name="PUSH THE BUTTON", _power=BlaineButton),
    Hero(name="Blue", ability_name = "Smell 'ya Later", _power=BlueSmell),
    Hero(name="Bruno", ability_name="Thicc Bod", _power=BrunoBod),
    Hero(name="Erika", ability_name="Herb Master", _power=ErikaGarden),
    Hero(name="Giovanni", ability_name="Crypto Dividends", _power=GiovanniGains),
    Hero(name='Green', ability_name='Mineral Collector', _power = GreensRocks),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution', _power = KogaNinja),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning', _power = JanineJutsu),
    Hero(name='Lance', ability_name='"Dragon" Master', _power = LanceFetish),
    Hero(name='Lt. Surge', ability_name='Gorilla Warfare', _power = SurgeGorilla),
    Hero(name='Misty', ability_name='Trust Fund', _power = MistyTrustFund),
    Hero(name='Red', ability_name='Plot Armor', _power = RedCheater),
    Hero(name='Jessie and James', ability_name='Blast Off!!', _power = BlastOff),
    Hero(name='Sabrina', ability_name='Clairvoyance', _power = SabrinaFuture), 
    Hero(name='Will', ability_name='Chunnibyou', _power = WillSac),
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
