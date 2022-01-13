# i need some class here that contains only the raw information about the game and its state
# and does not include things like factories
# this split needs to happen now so i can make the state be fully transmitted over the wire

# maybe we just do a `mutate` function or something
import typing as T
from enum import Enum
from pydantic import BaseModel

from engine.base import _Synchronized
from engine.match import Match
from engine.player import Player
from engine.turn import StageConfig

SHOP_SIZE = 5


class GamePhase(Enum):
    """
    Enumeration of game phases

    INITIALIZATION: setup the game
    TURN_SETUP: all game components should run turn setup actions
    TURN_PREP: enable user input and feed UI event loop callbacks into components
    TURN_EXECUTE: lock user input and run component execute actions
    TURN_CLEANUP: keep user input locked, report status here, prepare for next turn
    CLEANUP: final cleanup of all components, should enter the COMPLETED phase
    COMPLETED: issued when the game is over and all actors should cease all actions.
    ERROR: transition here when something goes wrong. No outward transitions.
    """

    INITIALIZATION = 0
    READY_TO_START = 1
    TURN_SETUP = 2
    TURN_DECLARE_TEAM = 3
    TURN_PREPARE_TEAM = 4
    TURN_PREP = 5
    TURN_EXECUTE = 6
    TURN_CLEANUP = 7
    TURN_COMPLETE = 8
    CLEANUP = 9
    COMPLETED = 10
    ERROR = 11


class State(BaseModel):
    """
    Game state

    Should only include data-members.

    This object should be shared with all clients and should allow for full representation of
    the game state.

    NOTE: it's probably better and safer to just dump the entire state every time we do a data
    transfer. We can (probably) get away with this because the amount of data that needs to
    be transferred is very low, and is at a relatively low frequency (100ms ticks).
    """

    phase: GamePhase
    players: T.List[Player]  # list of players in the game
    shop_window_raw: T.Dict[str, T.List[T.Optional[str]]]
    current_matches: T.List[Match]
    matches: T.List[T.List[Match]]
    turn_number: int
    stage: StageConfig = StageConfig(stage=0, round=0)
    t_phase_elapsed: float = 0.0
    t_phase_remaining: float = float('inf')

    @classmethod
    def default(cls):
        return cls(
            phase=GamePhase.INITIALIZATION,
            players=[],
            shop_window_raw={},
            current_matches=[],
            matches=[[]],
            turn_number=0,
        )

    @property
    def shop_window(self):
        return {
            player: self.shop_window_raw.get(player.id, [None] * SHOP_SIZE)
            for player in self.players
        }

    def get_player_by_id(self, id):
        matches = [x for x in self.players if str(x.id) == id]
        if len(matches) < 1:
            raise ValueError("No match found for player id {}".format(id))
        if len(matches) > 1:
            raise ValueError("More than 1 matching player???")
        return matches[0]

    @property
    def time_left_in_turn(self):
        return self.t_phase_remaining - self.t_phase_elapsed
