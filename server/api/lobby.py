"""
Lobby API

Supports high-level interfacing with games

TODO: store game models etc in database and not in internal memory fucking lmao
"""
import typing as T
from collections import namedtuple
from threading import Thread
from uuid import UUID

from fastapi.routing import APIRouter
from pydantic import BaseModel

from engine.env import Environment, GamePhase
from engine.player import EntityType, Player
from server.api.base import GameNotFound, PlayerContextRequest
from server.api.base import ReportingResponse
from server.api.player import Player as PlayerModel

lobby_router = APIRouter(prefix="/lobby")

ALL_GAMES: T.Dict[UUID, Environment] = {}  # map of game_id to game_object


@lobby_router.get("/all")
async def get_all_games():
    return [x for x in ALL_GAMES]


class CreateGameRequest(BaseModel):
    number_of_players: int = 8


class CreateGameResponse(BaseModel):
    game_id: str


PlayerContext = namedtuple("PlayerContext", ["game", "player"])


def get_request_context(request: PlayerContextRequest) -> T.Tuple[Environment, PlayerModel]:
    """
    Given an incoming request, determine what game and player the request is meant for.

    TODO: this pattern sucks ass, should do namespaced APIs
    """
    player = request.player
    game_id = UUID(request.game_id)

    game = ALL_GAMES.get(game_id)
    if game is not None:
        return PlayerContext(game=game, player=player)
    print(ALL_GAMES)
    raise GameNotFound(f"No game with ID {game_id}")


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
        player = Player(name=player_model.name, type=EntityType.HUMAN, id=player_model.id)
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


class StartGameRequest(BaseModel):
    """
    Start a game by ID
    """
    game_id: str


@lobby_router.post("/start")
async def start_game(request: StartGameRequest):
    """
    Start a game
    """
    game_id = UUID(request.game_id)
    game = ALL_GAMES.get(game_id)
    if game is not None:
        # call initialize on the game and then start the game loop
        game.initialize()
        # TODO: insert game loop stuff here
        game.phase = GamePhase.TURN_SETUP

        # start a game thread???
        def run_loop():
            while True:
                game.step_loop()
        thread = Thread(target=run_loop)
        thread.daemon = True
        thread.start()
        if game.is_running:
            return ReportingResponse(success=True)

    return ReportingResponse(success=False, message="Failed to start game")
