"""
WebSockets Client Helpers

Primarily deals with the asynchronous implementation
"""
import asyncio
import json
import aiohttp
import typing as T
from engine.models.party import PartyConfig
from server.api.base import ReportingResponse
from server.api.websocket import AddToTeam, MoveToParty, MoveToStorage, ReleaseFromParty, ReleaseFromStorage, UpdatePartyConfig
from server.api.websocket import CatchShop
from server.api.websocket import RemoveFromTeam
from server.api.websocket import RollShop
from server.api.websocket import ShiftTeamDown
from server.api.websocket import ShiftTeamUp

from utils.context import GameContext

if T.TYPE_CHECKING:
    from pydantic import BaseModel
    from aiohttp.client import ClientWebSocketResponse
    from websockets.legacy.client import WebSocketClientProtocol


class WebSocketClient:
    """
    WebSocket client object
    """

    def __init__(self, client):
        loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=loop)
        self.client: ClientWebSocketResponse = client

    async def disconnect(self):
        self.client = await self.client.close()

    async def send_request(self, endpoint: str, request: "BaseModel", response_type: ReportingResponse):
        """
        Issue a request. Record exceptions.

        response_type right now should be ReportingResponse by default
        """

        # format into request type
        # TODO: write a BaseModel for this
        formatted = {"endpoint": endpoint, "payload": request.json()}

        try:
            await self.client.send(json.dumps(formatted))
            raw = await self.client.recv()
            response = response_type.parse_raw(json.loads(raw))
            if not response.success:
                raise RuntimeError(f"Websocket remote error: {response.message}")
        except Exception as exc:
            print(f'Encountered exception in WebSocket client: {repr(exc)}')

    async def implement_api_client(self, api_class, context: GameContext, **kwargs):
        """
        Take an API class object and formulate the correct input for it.

        Assumes that the request is a class that inherits WebSocketPlayerRequest
        """
        request_type = api_class.REQUEST_TYPE
        request = request_type.from_game_context(context, **kwargs)
        await self.send_request(api_class.__name__, request, response_type=ReportingResponse)

    # oh fucking boy time to redo the API implementations
    # SHOP APIs
    async def roll_shop(self, context: GameContext):
        """
        Roll the Shop
        """
        await self.implement_api_client(RollShop, context)

    async def catch_pokemon(self, context: GameContext, shop_index: int):
        """
        Catch a Pokemon
        """
        await self.implement_api_client(CatchShop, context, shop_index=shop_index)

    # PARTY CONFIG APIs
    async def update_party_config(self, context: GameContext, party_config: PartyConfig):
        """
        Update a party config
        """
        await self.implement_api_client(UpdatePartyConfig, context, party_config=party_config)

    # TEAM APIs
    async def shift_team_up(self, context: GameContext, team_index: int):
        """
        Shift a team member up
        """
        await self.implement_api_client(ShiftTeamUp, context, team_index=team_index)

    async def shift_team_down(self, context: GameContext, team_index: int):
        """
        Shift a team member down
        """
        await self.implement_api_client(ShiftTeamDown, context, team_index=team_index)

    async def remove_team_member(self, context: GameContext, team_index: int):
        """
        Remove team member
        """
        await self.implement_api_client(RemoveFromTeam, context, team_index=team_index)

    # PARTY APIs
    async def add_to_team(self, context: GameContext, party_index: int):
        """
        Add party member to team
        """
        await self.implement_api_client(AddToTeam, context, party_index=party_index)

    async def release_from_party(self, context: GameContext, party_index: int):
        """
        Release party member from team
        """
        await self.implement_api_client(ReleaseFromParty, context, party_index=party_index)

    async def move_to_storage(self, context: GameContext, party_index: int):
        """
        Move party to storage
        """
        await self.implement_api_client(MoveToStorage, context, party_index=party_index)

    # STORAGE APIs
    async def move_to_party(self, context: GameContext, storage_index: int):
        await self.implement_api_client(MoveToParty, context, storage_index=storage_index)

    async def release_from_storage(self, context: GameContext, storage_index: int):
        await self.implement_api_client(ReleaseFromStorage, context, storage_index=storage_index)
