"""
Battle Models
"""
import typing as T
from enum import Enum
from pydantic import BaseModel

from engine.models.base import Entity
from engine.models.enums import Move
from engine.utils.gamemaster import gamemaster


class BattleStatus(Enum):

    UNKNOWN = 0
    DID_NOT_BATTLE = 1
    BATTLED = 2
    FAINTED = 3


class BattleStat(BaseModel):
    """
    Combat statistics
    """
    poke_id: str
    damage_taken: float
    damage_dealt: float
    battle_status: BattleStatus

    def __str__(self):
        # TODO: add BattleStatus
        return f"Dealt {self.damage_dealt}, received {self.damage_taken}"


class BattleSummary(BaseModel):
    """
    Should summarize Pokemon combat result
    """

    winner: str  # oneof player1_id, player2_id
    player1_id: str
    player2_id: str
    team1: T.List[str]  # a list of pokemon IDs that participated in combat
    team2: T.List[str]
    battle_stats: T.Dict[str, BattleStat]  # maps pokemon IDs to their battle statistics


class Event:
    def __init__(self, sequence_number, category, value, time = None):
        self.id: int = sequence_number
        self.type: str = category
        self.value: str = value


class BattleEvent(BaseModel):
    
    seq: int  # sequence number
    timestamp: float  # timestamp of the battle event
    category: str  # type of event (loosely typed for now)
    value: str  # message


class BattleRenderLog(BaseModel):
    """
    Encapsulates an HTML document that can render a battle
    """

    success: bool = True  # TODO: de-conflate
    render: str
