# i need some class here that contains only the raw information about the game and its state
# and does not include things like factories
# this split needs to happen now so i can make the state be fully transmitted over the wire

# maybe we just do a `mutate` function or something
import codecs
from io import StringIO
import typing as T
from pydantic import BaseModel, PrivateAttr, StrBytes
from pydantic import Field
from engine.models.association import Association, PlayerRoster, PlayerShop
from engine.models.association import PlayerInventory
from engine.models.hero import Hero
from engine.models.items import Item
from engine.models.phase import GamePhase
from engine.models.pokemon import Pokemon
from engine.models.shop import ShopOffer
from engine.models.stage_config import StageConfig
from engine.models.player import Player
from engine.models.match import Match
from engine.models.weather import WeatherType

if T.TYPE_CHECKING:
    pass

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
    creeps: T.List["Player"] = list()  # list of creep players in the game

    current_matches: T.List["Match"]
    turn_number: int
    stage: StageConfig = StageConfig(stage=0, round=0)
    t_global: float = 0.0  # global timer
    t_phase_elapsed: float = 0.0
    t_phase_duration: float = float('inf')

    # NOTE: registries are to ensure that these objects do not garbage collected until
    # the state object is destructed. They should not be transmitted over the wire.
    # TODO: figure out why pydantic breaks if the type is set
    _pokemon_registry: T.List[Pokemon] = PrivateAttr(default_factory=list)
    _item_registry: T.List[T.Any] = PrivateAttr(default_factory=list)  # TODO: fix type annotation
    _associations: T.List[Association] = PrivateAttr(default_factory=list)

    # server keeps track of associations and instances
    # client just gets object copies

    # Shop containers
    shop_window_raw: T.Dict[str, T.List[T.Optional[ShopOffer]]] = dict()

    # Pokemon containers
    player_roster_raw: T.Dict[str, T.List[Pokemon]] = dict()

    # Inventory containers
    player_inventory_raw: T.Dict[str, T.List[T.Any]] = dict()  # maps player ID to a list of items

    # Player hero associations
    player_hero: T.Dict[str, Hero] = dict()  # maps player ID to their hero

    # Turn Weather
    weather: WeatherType = WeatherType.NONE

    def load_containers(self):
        self.shop_window_raw = {p.id: PlayerShop.get_shop(p) for p in self.players}
        self.player_roster_raw = {p.id: PlayerRoster.get_roster(p) for p in self.players}
        self.player_inventory_raw = {p.id: PlayerInventory.get_inventory(p) for p in self.players}

    def for_player(self, player: Player):
        """
        Generate a state object to transmit over the wire to a player.

        Should be isolated to only the information a specific player requires.

        For example, a player only needs to know about what is in their shop specifically.
        Information pertaining to another players' shop is not required.

        Isolated components:
        * shop_window
        * pokemon
        * items
        """
        shop_window = {player.id: self.shop_window_raw[player.id]}
        player_inventory = {player.id: self.player_inventory_raw[player.id]}
        player_roster = {player.id: self.player_roster_raw[player.id]}
        # only transmit the creep if player is against them
        creeps = []
        for match in self.current_matches:
            if match.has_player(player):
                if match.player1 == player and match.player2.is_creep:
                    creeps.append(match.player2)
                    break
                elif match.player2 == player and match.player1.is_creep:
                    creeps.append(match.player1)
                    break

        return self.__class__(
            phase=self.phase,
            players=self.players,
            creeps=creeps,
            shop_window_raw=shop_window,
            current_matches=self.current_matches,
            turn_number=self.turn_number,
            player_inventory_raw=player_inventory,
            player_roster_raw=player_roster,
            stage=self.stage,
            t_phase_elapsed=self.t_phase_elapsed,
            t_phase_duration=self.t_phase_duration,
            player_hero=self.player_hero,
            weather=self.weather,
        )

    @classmethod
    def default(cls):
        return cls(
            phase=GamePhase.INITIALIZATION,
            players=[],
            current_matches=[],
            turn_number=0,
        )

    @classmethod
    def parse_raw(cls, b: StrBytes, decompress=True, **kwargs):
        """
        By default assume this message is compressed
        """
        if not decompress:
            return super().parse_raw(b, **kwargs)
        return super().parse_raw(codecs.decode(b, 'zlib'), **kwargs)

    def json(self, *args, compress=True, **kwargs):
        """
        By default compress this message
        """
        self.load_containers()
        if not compress:
            return super().json(*args, **kwargs)
        return codecs.encode(bytes(super().json(*args, **kwargs), 'ascii'), 'zlib')

    def dict(self, *args, **kwargs):
        """
        Re-load containers every time
        """
        self.load_containers()
        return super().dict(*args, **kwargs)

    @property
    def player_inventory(self):
        """
        Return all player inventories
        """
        self.load_containers()
        return {p: self.player_inventory_raw.get(p.id) for p in self.players}

    @property
    def player_roster(self):
        """
        Return all player rosters
        """
        self.load_containers()
        return {p: self.player_roster_raw.get(p.id) for p in self.players}

    @property
    def shop_window(self):
        self.load_containers()
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
        return self.t_phase_duration - self.t_phase_elapsed
