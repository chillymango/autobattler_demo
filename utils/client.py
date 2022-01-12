"""
FastAPI Client

Abstracts things like connecting to the game server and making requests
"""
import aiohttp
import json
import requests
from types import MethodType
from uuid import uuid4

from pydantic import BaseModel

# make request imports from API modules
from server.api.base import ReportingResponse
from server.api.base import PlayerContextRequest
from server.api.lobby import CreateGameRequest, PlayerContext, StartGameRequest
from server.api.lobby import CreateGameResponse
from server.api.lobby import DeleteGameRequest
from server.api.lobby import JoinGameRequest
from server.api.lobby import LeaveGameRequest
from server.api.player import Player as PlayerModel
from server.api.shop import CatchPokemonRequest
from utils.context import GameContext


class ServerRequestFailure(Exception):
    """
    Usually suggests a handled failure
    """


class GameServerClient:
    """
    Really just for debugging for now...

    Really looking like the monorepo design is coming in soon lol
    """

    def __init__(self, bind="http://localhost:8000"):
        self.bind = bind

    def get(self, endpoint, **kwargs) -> str:
        addr = "{}/{}".format(self.bind, endpoint)
        print("Issuing get request to {}".format(addr))
        response = requests.get(addr, **kwargs)
        if response.status_code == 200:
            return response.text
        response.raise_for_status()

    def post(self, endpoint: str, data: BaseModel, response_type=BaseModel, **kwargs):
        addr = "{}/{}".format(self.bind, endpoint)
        print("Issuing post request to {}".format(addr))
        response = requests.post(addr, data.json(), **kwargs)
        if response.status_code == 200:
            return response_type.parse_raw(response.text)
        response.raise_for_status()

    def get_games(self):
        """
        Issue a request to get all current games
        """
        return json.loads(self.get("lobby/all"))

    def create_game(self, number_of_players: int = 8):
        """
        Issue a create game request
        """
        request = CreateGameRequest(number_of_players=number_of_players)
        return self.post("lobby/create", request, response_type=CreateGameResponse)

    def delete_game(self, game_id: str, force: bool = False):
        """
        Issue a delete game request
        """
        request = DeleteGameRequest(game_id=game_id, force=force)
        response = self.post("lobby/delete", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def join_game(self, game_id: str, player: PlayerModel):
        """
        Have a player join the game
        """
        request = JoinGameRequest(game_id=game_id, player=player)
        response = self.post("lobby/join", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def leave_game(self, game_id: str, player: PlayerModel):
        """
        Have a player leave a game
        """
        request = LeaveGameRequest(game_id=game_id, player=player)
        response = self.post("lobby/leave", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def start_game(self, game_id: str):
        """
        Start a game
        """
        request = StartGameRequest(game_id=game_id)
        response = self.post("lobby/start", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    def get_players(self, game_id: str):
        """
        Get the list of players in a game
        """
        return json.loads(self.get("game/players", params={'game_id': game_id}))

    def roll_shop(self, game_context: GameContext):
        """
        Roll shop for a player
        """
        request = PlayerContextRequest.from_game_context()
        response = self.post("shop/roll", request, response_type=ReportingResponse)
        if not response.success:
            print(response.message)

    def catch_pokemon(self, game_context: GameContext, shop_index: int):
        """
        Catch Pokemon at some index in a shop for a player.
        """
        request = CatchPokemonRequest.from_game_context(game_context)
        request.shop_index = shop_index
        response = self.post("shop/catch", request, response_type=ReportingResponse)
        if not response.success:
            print(response.message)


class AsynchronousServerClient(GameServerClient):
    """
    Override the get and post requests and use aiohttp
    """

    # wrap all methods
    def __init__(self, bind="http://localhost:8000"):
        super().__init__(bind=bind)

        # turn all functions into a coroutine
        for attrname in dir(self):
            if attrname.startswith('_'):
                continue
            attr = getattr(self, attrname)

            if isinstance(attr, MethodType):
                # replace with a coroutine wrapper
                async def __coro__():
                    return attr(self)
                setattr(self, attrname, __coro__)

    async def get(self, *args, **kwargs):
        addr = '/'.join(self.bind, args[0])
        with aiohttp.ClientSession() as session:
            await session.get(addr)


if __name__ == "__main__":
    # Asynchronous Test
    import asyncio
    async_client = AsynchronousServerClient()
    asyncio.gather([async_client.get_games(), async_client.get_games()])
    #client = GameServerClient()
    test_player = PlayerModel(id=str(uuid4()), name='Albert Yang')
    import IPython; IPython.embed()
