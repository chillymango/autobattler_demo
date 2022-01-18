# i need some class here that contains only the raw information about the game and its state
# and does not include things like factories
# this split needs to happen now so i can make the state be fully transmitted over the wire

# maybe we just do a `mutate` function or something
import typing as T
from pydantic import BaseModel
from engine.match import Match
from engine.player import Player
from utils.phase import GamePhase
from engine.models.stage_config import StageConfig


SHOP_SIZE = 5


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

    phase: "GamePhase"
    players: T.List["Player"]  # list of players in the game
    shop_window_raw: T.Dict[str, T.List[T.Optional[str]]]
    current_matches: T.List["Match"]
    turn_number: int
    stage: StageConfig = StageConfig(stage=0, round=0)
    t_phase_elapsed: float = 0.0
    t_phase_duration: float = float('inf')

    @classmethod
    def default(cls):
        return cls(
            phase=GamePhase.INITIALIZATION,
            players=[],
            shop_window_raw={},
            current_matches=[],
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
    def alive_players(self):
        return [player for player in self.players]

    @property
    def time_left_in_turn(self):
        return self.t_phase_duration - self.t_phase_elapsed
