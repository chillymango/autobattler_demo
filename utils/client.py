"""
FastAPI Client

Abstracts things like connecting to the game server and making requests
"""
import aiohttp
import asyncio
import concurrent.futures
import json
import logging
import requests
from threading import Thread
import time
import typing as T
import weakref
from types import MethodType
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from engine.player import Player

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
from server.api.team import AddToTeamRequest, ShiftRequest
from server.api.team import RemoveFromTeamRequest
from utils.context import GameContext


class ServerRequestFailure(Exception):
    """
    Usually suggests a handled failure
    """

nullplayer = PlayerModel(id='nullplayer', name='nullplayer')


class AsyncLoopThread(Thread):
    def __init__(self, coro, loop):
        super().__init__(daemon=True)
        self.coro = coro
        self.loop = loop
        self._returned = False
        self._value = None

    @property
    def value(self):
        if not self._returned:
            raise ValueError("Coroutine hasn't finished yet")
        return self._value

    def run(self):
        future = asyncio.run_coroutine_threadsafe(self.coro, self.loop)
        self._value = future.result()
        self._returned = True


class CoroutineProxy:
    """
    I actually bet this will work

    Wrap a class method as a callable that returns a coroutine which should
    implement the synchronous client behavior.
    """

    def __init__(self, method):
        self.method = method

    def run_task_in_thread(self, coro, loop):
        """
        runs in thread
        """
        asyncio.run_coroutine_threadsafe(coro, loop)

    def __call__(self, *args, **kwargs):
        # create another event loop in another thread and run the request there
        
        loop = asyncio.get_event_loop()
        # TODO: this doesn't actually work with QEventLoop in QApplication right now
        coro = self.method(*args, **kwargs)
        task = loop.create_task(coro)
        loop.run_until_complete(task)
        return task.result()


class AsynchronousServerClient:
    """
    Override the get and post requests and use aiohttp
    """

    # wrap all methods
    def __init__(self, bind="http://localhost:8000", loop=None):
        self.bind = bind
        if loop:
            self.session = aiohttp.ClientSession(loop=loop)
        else:
            self.session = aiohttp.ClientSession(loop=asyncio.get_event_loop())

    async def get(self, endpoint, **kwargs) -> aiohttp.ClientResponse:
        addr = '/'.join([self.bind, endpoint])
        return await self.session.get(addr, **kwargs)

    async def post(self, endpoint: str, data: BaseModel, response_type=BaseModel, **kwargs):
        addr = '/'.join([self.bind, endpoint])
        async with self.session.post(addr, json=data.dict(), **kwargs) as response:
            if response.status == 200:
                return response_type.parse_raw(await response.text())
            response.raise_for_status()

    async def get_games(self):
        """
        Issue a request to get all current games
        """
        return json.loads(await self.get("lobby/all"))

    async def create_game(self, number_of_players: int = 8):
        """
        Issue a create game request
        """
        request = CreateGameRequest(number_of_players=number_of_players)
        return await self.post("lobby/create", request, response_type=CreateGameResponse)

    async def delete_game(self, game_id: str, force: bool = False):
        """
        Issue a delete game request
        """
        request = DeleteGameRequest(game_id=game_id, force=force)
        response = await self.post("lobby/delete", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def join_game(self, game_id: str, player: PlayerModel):
        """
        Have a player join the game
        """
        request = JoinGameRequest(game_id=game_id, player=player)
        response = await self.post("lobby/join", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def leave_game(self, game_id: str, player: PlayerModel):
        """
        Have a player leave a game
        """
        request = LeaveGameRequest(game_id=game_id, player=player)
        response = await self.post("lobby/leave", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def start_game(self, game_id: str):
        """
        Start a game
        """
        request = StartGameRequest(game_id=game_id)
        response = await self.post("lobby/start", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def get_players(self, game_id: str):
        """
        Get the list of players in a game
        """
        return json.loads(await self.get("game/players", params={'game_id': game_id}))

    async def roll_shop(self, game_context: GameContext):
        """
        Roll shop for a player
        """
        try:
            request = PlayerContextRequest.from_game_context(game_context)
            response = await self.post("shop/roll", request, response_type=ReportingResponse)
            if not response.success:
                print(response.message)
        except Exception as exc:
            print(repr(exc))
            raise

    async def catch_pokemon(self, game_context: GameContext, shop_index: int):
        """
        Catch Pokemon at some index in a shop for a player.
        """
        print('doing catch request')
        try:
            request = CatchPokemonRequest.from_game_context(game_context, shop_index=shop_index)
            response = await self.post("shop/catch", request, response_type=ReportingResponse)
        except Exception as exc:
            print(repr(exc))
            raise
        if not response.success:
            print(response.message)

    # NOTE: for team functions, for now we will just implement individual requests for adjusting
    # teams discretely per requested operation, instead of asking for a team change. This will
    # probably not scale but i'm not worried about that yet
    # backend still responsible for handling validation
    async def shift_team_member_up(self, ctx: PlayerContextRequest, idx: int):
        """
        ctx: player context
        idx: index of pokemon to shift upwards
        """
        print('doing shift team member request')
        try:
            request = ShiftRequest.from_game_context(ctx, index=idx)
            response = await self.post("team/shift_up", request, response_type=ReportingResponse)
        except Exception as exc:
            print(repr(exc))
            raise
        if not response.success:
            print(response.message)

    async def shift_team_member_down(self, ctx: PlayerContextRequest, idx: int):
        """
        ctx: player context
        idx: index of pokemon to shift downwards
        """
        print('doing shift team member request')
        try:
            request = ShiftRequest.from_game_context(ctx, index=idx)
            response = await self.post("team/shift_down", request, response_type=ReportingResponse)
        except Exception as exc:
            print(repr(exc))
            raise
        if not response.success:
            print(response.message)

    async def add_to_team(self, ctx: PlayerContextRequest, idx):
        """
        ctx: player context
        idx: index of pokemon to remove
        """
        try:
            request = AddToTeamRequest.from_game_context(ctx, party_idx=idx)
            response = await self.post("team/add", request, response_type=ReportingResponse)            
        except Exception as exc:
            print(repr(exc))
            raise
        if not response.success:
            print(response.message)

    async def remove_from_team(self, ctx: PlayerContextRequest, idx):
        """
        ctx: player context
        idx: index of pokemon to remove
        """
        try:
            request = RemoveFromTeamRequest.from_game_context(ctx, team_idx=idx)
            response = await self.post("team/remove", request, response_type=ReportingResponse)
        except Exception as exc:
            print(repr(exc))
            raise
        if not response.success:
            print(response.message)

    # debug functions
    async def add_pokeballs(self, ctx: PlayerContextRequest):
        """
        Add 100 Pokeballs
        """
        return await self.post("debug/add_pokeballs", ctx, response_type=ReportingResponse)

    async def add_energy(self, ctx: PlayerContextRequest):
        """
        Add 100 Energy
        """
        return await self.post("debug/add_energy", ctx, response_type=ReportingResponse)

    async def get_games(self):
        """
        Issue a request to get all current games
        """
        response = await self.get("lobby/all")
        json_res = await response.json()
        return json_res

    async def advance_turn(self, game_id: T.Union[str, UUID]):
        """
        Issue a request to advance the turn by 1
        """
        game_id = str(game_id)
        request = PlayerContextRequest(game_id=game_id, player=nullplayer)
        response = await self.post("debug/advance_turn", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def retract_turn(self, game_id: T.Union[str, UUID]):
        game_id = str(game_id)
        request = PlayerContextRequest(game_id=game_id, player=nullplayer)
        response = await self.post("debug/retract_turn", request, response_type=ReportingResponse)
        if not response.success:
            raise ServerRequestFailure(response.message)

    async def make_new_matches(self, game_id: T.Union[str, UUID]):
        """
        Issue a request to make new matches
        """
        game_id = str(game_id)
        request = PlayerContextRequest(game_id=game_id, player=nullplayer)
        response = await self.post("debug/new_matches", request, response_type=ReportingResponse)
        print('i am out?')
        if not response.success:
            raise ServerRequestFailure(response.message)


class GameServerClient(AsynchronousServerClient):
    """
    Synchronous version of the server client.

    All coroutines defined in the async client are wrapped with a proxy callable that will
    await and return the output.
    """

    BUILTINS = ['get', 'post']

    def __init__(self, bind="http://localhost:8000"):
        super().__init__(bind=bind)  # probably don't need to support a loop argument?

        # turn all functions into a coroutine
        for attrname in dir(self):
            if attrname.startswith('_'):
                continue
            if attrname in self.BUILTINS:
                continue

            attr = getattr(self, attrname)

            if isinstance(attr, MethodType):
                # replace with a coroutine wrapper
                hidden_attr = f"__{attrname}"
                setattr(self, hidden_attr, attr)
                base = getattr(self, hidden_attr)

                setattr(self, attrname, CoroutineProxy(base))


if __name__ == "__main__":
    test_player = PlayerModel(id=str(uuid4()), name='Albert Yang')

    # Asynchronous Test
    async def testing():
        async_client = AsynchronousServerClient()
        #game = await async_client.create_game()
        await async_client.start_game('673b70ca-7ee4-4013-86b3-342eda0d3d02')
        #print(game)
        #await async_client.join_game(game.game_id, test_player)
        #await async_client.start_game(game.game_id)
        #ctx = PlayerContextRequest(player=test_player, game_id=game.game_id)
        #await async_client.add_pokeballs(ctx)

    asyncio.run(testing())

    # Synchronous Test
    #client = GameServerClient()
    #game = client.create_game()

    #import IPython; IPython.embed()
