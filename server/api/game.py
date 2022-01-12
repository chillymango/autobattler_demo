"""
Individual game API

Supports inspection of some high-level game data
"""
import typing as T
from uuid import UUID

from fastapi.routing import APIRouter
from pydantic import BaseModel
from engine.env import Environment

from server.api.lobby import ALL_GAMES
from server.api.player import Player as PlayerModel

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.state import State

game_router = APIRouter(prefix="/game")


class GamePlayersResponse(BaseModel):
    players: T.List[PlayerModel]  # list of player objects


@game_router.get("/players", response_model=GamePlayersResponse)
async def get_game_players(game_id: str = None):
    """
    Return the list of players in a game
    """
    if game_id is None:
        raise ValueError("No game_id provided to request")

    game: "Environment" = ALL_GAMES.get(UUID(game_id))
    state: "State" = game.state
    if game is None:
        raise ValueError("No game with id {} found".format(game_id))

    return GamePlayersResponse(players=[PlayerModel.from_player_object(x) for x in state.players])


class GameStateResponse(BaseModel):
    state_json_str: str  # JSON string representing the state object


@game_router.get("/state", response_model=GameStateResponse)
async def get_game_state(game_id: str = None):
    """
    Return the game state

    NOTE: this is primarily for debugging, real game state should be transmitted over pubsub
    """
    if game_id is None:
        raise ValueError("No game_id provided to request")

    game = ALL_GAMES.get(UUID(game_id))
    if game is None:
        raise ValueError("No game with id {} found".format(game_id))

    state = game.state
    return GameStateResponse(state_json_str=state.json())
