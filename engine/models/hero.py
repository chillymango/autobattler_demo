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
    power: PlayerHeroPower = None  # TODO: make this not default


NORMAL_HEROES: T.List[Hero] = [
    Hero(name="Brock", ability_name="Rock Solid", power=BrockShieldPower),
    Hero(name="Blaine", ability_name="PUSH THE BUTTON", power=BlaineButton),
    Hero(name="Blue", ability_name = "Smell 'ya Later", power=BlueSmell),
    Hero(name="Bruno", ability_name="Thicc Bod", power=BrunoBod),
    Hero(name="Erika", ability_name="Herb Master", power=ErikaGarden),
    Hero(name="Giovanni", ability_name="Crypto Dividends", power=GiovanniGains),
    Hero(name='Green', ability_name='Mineral Collector', power = GreensRocks),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution', power = KogaNinja),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning', power = JanineJutsu),
    Hero(name='Lance', ability_name='"Dragon" Master', power = LanceFetish),
    Hero(name='Lt. Surge', ability_name='Gorilla Warfare', power = SurgeGorilla),
    Hero(name='Misty', ability_name='Trust Fund', power = MistyTrustFund),
    Hero(name='Red', ability_name='Plot Armor', power = RedCheater),
    Hero(name='Jessie and James', ability_name='Blast Off!!', power = BlastOff),
    Hero(name='Sabrina', ability_name='Clairvoyance',power = SabrinaFuture), 
    Hero(name='Will', ability_name='Chunnibyou', power = WillSac),

    
]

PRISMATIC_HEROES: T.List[Hero] = [
    # TODO: fill out
    Hero(name="Brock", ability_name="Rock Solid", power=None),
    Hero(name="Blaine", ability_name="Blaze It", power=None),
    Hero(name="Blue", ability_name = "Smell 'ya Later", power=None),
    Hero(name="Bruno", ability_name="Thicc Bod", power=None),
    Hero(name="Erika", ability_name="Herb Master", power=None),
    Hero(name="Giovanni", ability_name="Crypto Dividends", power=None),
    Hero(name='Green', ability_name='Mineral Collector'),
    Hero(name='Janine', ability_name='Ninjutsu Art of Substitution'),
    Hero(name='Koga', ability_name='Ninjutsu Art of Summoning'),
    Hero(name='Lance', ability_name='"Dragon" Master')
]

HERO_CONTEXT: T.Dict[Hero, str] = {}
