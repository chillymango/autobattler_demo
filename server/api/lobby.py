"""
Lobby API

Supports high-level interfacing with games

TODO: store game models etc in database and not in internal memory fucking lmao
"""
import sys
import typing as T
from uuid import UUID

from fastapi.routing import APIRouter
from pydantic import BaseModel

from api.base import ReportingResponse
from api.player import Player as PlayerModel
from engine.env import Environment
from engine.player import Player

lobby_router = APIRouter(prefix="/lobby")

ALL_GAMES: T.Dict[UUID, Environment] = {}  # map of game_id to game_object


@lobby_router.get("/all")
async def get_all_games():
    return [x for x in ALL_GAMES]


class CreateGameRequest(BaseModel):
    number_of_players: int = 8


class CreateGameResponse(BaseModel):
    game_id: str


@lobby_router.post("/create")
async def create_game(request: CreateGameRequest):
    """
    Create a game
    """
    game = Environment(request.number_of_players)
    ALL_GAMES[game.id] = game
    # make publisher start broadcasting game state
    return CreateGameResponse(game_id=str(game.id))


class DeleteGameRequest(BaseModel):
    """
    Delete a game.

    If `force` is set to True, will delete the game, even if it is still in progress.
    """
    game_id: str
    force: bool = False


@lobby_router.post("/delete")
async def delete_game(request: DeleteGameRequest):
    """
    Delete a game
    """
    game_id = UUID(request.game_id)
    game = ALL_GAMES.get(game_id)
    if game is not None:
        if game.is_running:
            if request.force:
                message = (
                    "Game {} is active. To force delete, specify `force=True` in request"
                    .format(game.id)
                )
                return ReportingResponse(success=False, message=message)

        ALL_GAMES.pop(game_id)
        return ReportingResponse(success=True)

    return ReportingResponse(
        success=False,
        message="No game found with id {}".format(game_id)
    )


class JoinGameRequest(BaseModel):
    """
    Have a player join a game.

    Player model should specify their name and their player ID.
    """

    game_id: str
    player: PlayerModel


@lobby_router.post("/join")
async def join_game(request: JoinGameRequest):
    """
    Join a game by ID
    """
    game_id = UUID(request.game_id)
    game = ALL_GAMES.get(game_id)
    if game is not None:
        if game.is_running:
            return ReportingResponse(success=False, message="Requested game has already started")
        if game.is_finished:
            return ReportingResponse(success=False, message="Game has already finished")

        # create player from player model
        player_model = request.player
        player = Player(name=player_model.name)
        try:
            game.add_player(player)
            return ReportingResponse(success=True)
        except Exception as err:
            return ReportingResponse(success=False, message=repr(err))

    return ReportingResponse(success=False, message="No game found with id ")


class LeaveGameRequest(BaseModel):
    """
    Have a player leave a game.

    Player model should specify their name and their player ID.
    """

    game_id: str
    player: PlayerModel


@lobby_router.post("/leave")
async def leave_game(request: LeaveGameRequest):
    """
    Leave a game by ID
    """
    game_id = UUID(request.game_id)
    game = ALL_GAMES.get(game_id)
    if game is not None:
        # create player from player model
        player_model = request.player
        player = Player(name=player_model.name)
        try:
            game.remove_player(player)
            return ReportingResponse(success=True)
        except Exception as err:
            return ReportingResponse(success=False, message=repr(err))

    return ReportingResponse(success=False, message="No game found with id ")
