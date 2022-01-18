"""
Shared game context
"""
import typing as T
from collections import namedtuple

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.player import Player

GameContext: T.Tuple["Environment", "Player"] = namedtuple("GameContext", ["game", "player"])
