"""
WebSockets for reactive buttons
"""
import json
import sys
import traceback
import typing as T
from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import BaseModel

from engine.models.party import PartyConfig
from engine.player import PlayerManager
from server.api.base import PlayerContextRequest
from server.api.base import ReportingResponse
from server.api.base import WebSocketRequest
from server.api.lobby import get_request_context

if T.TYPE_CHECKING:
    from engine.player import Player
    from engine.shop import ShopManager
    from engine.models.state import State
    from engine.turn import Turn

ws_router = APIRouter(prefix="/webs")

# message structure should look something like:
# message = {
#   "timestamp": 1642224713.6656525
#   "request_type": "BaseModel",
#   "payload": {
#      "id": ...
#   }
# }

PARTY_SIZE = 6


class WebSocketPlayerRequest(PlayerContextRequest, WebSocketRequest):
    """
    Contains player context base and WebSocket marker
    """


@ws_router.websocket("/game_buttons")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            # load a request
            request = await websocket.receive_json()
            try:
                endpoint = request['endpoint']
                print(f'WS {endpoint}')
            except Exception as exc:
                print(f'WS ERROR: {repr(exc)}')
            api = get_request_endpoint_by_name(endpoint)
            payload = request['payload']

            # TODO: drop requests that are too time-different

            request_type = api.REQUEST_TYPE
    
            # hydrate the request
            hydrated = request_type(**json.loads(payload))
    
            # fulfill request
            callback = DISPATCHER.get(endpoint)
            if callback is None:
                raise ValueError(f"No WebSocket callback for {request_type.__name__}")
    
            # NOTE: this should happen synchronously
            response = callback(hydrated)
            await websocket.send_json(response.json())
        except WebSocketDisconnect:
            print('Breaking WebSocket connection')
            break
        except Exception as exc:
            # ignore this request and keep going
            # TODO: remove this in production to obfuscate internals
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            print(f'Error in websocket: {repr(exc)}')
            # still need to send an error response
            response = ReportingResponse(success=False, message=repr(exc))
            await websocket.send_json(response.json())


class WebSocketCallback:
    """
    All APIs and game button interactions should be defined through this class
    """

    REQUEST_TYPE = WebSocketPlayerRequest

    @staticmethod
    def callback(hydrated: "BaseModel"):
        """
        API function goes here
        """
        raise NotImplementedError


class AdvanceTurnRequest(WebSocketPlayerRequest):
    """
    Advance the turn by one
    """


class AdvanceTurn(WebSocketCallback):
    """
    Advance the turn by one
    """

    REQUEST_TYPE = AdvanceTurnRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        game, _ = get_request_context(hydrated)
        turn: "Turn" = game.turn
        turn.advance()
        return ReportingResponse(success=True)


class CatchPokemonRequest(WebSocketPlayerRequest):

    shop_index: int


class CatchShop(WebSocketCallback):
    """
    Catch a Pokemon for a player
    """

    REQUEST_TYPE = CatchPokemonRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)

        shop_manager: ShopManager = game.shop_manager
        shop_manager.catch(player, hydrated.shop_index)

        return ReportingResponse(success=True)


class RollShopRequest(WebSocketPlayerRequest):
    """
    Roll the shop for a player
    """


class RollShop(WebSocketCallback):

    REQUEST_TYPE = RollShopRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        game, player_model = get_request_context(hydrated)
        state: "State" = game.state
        player = state.get_player_by_id(player_model.id)
    
        shop_manager: "ShopManager" = game.shop_manager
        shop_manager.roll(player)
    
        return ReportingResponse(success=True)


class TeamMemberRequest(WebSocketPlayerRequest):
    """
    Modify a team member.

    Supported operations:
     * shift up
     * shift down
     * remove from team
    """

    team_index: int


class ShiftTeamUp(WebSocketCallback):
    """
    Shift a team member up
    """

    REQUEST_TYPE = TeamMemberRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.team_index
        game, player_model = get_request_context(hydrated)
        state: "State" = game.state
        player: Player = state.get_player_by_id(player_model.id)
        if idx < 1:
            return ReportingResponse(success=False, message="Pokemon is already at top")
        player.team[idx], player.team[idx - 1] = player.team[idx - 1], player.team[idx]
        return ReportingResponse(success=True)


class ShiftTeamDown(WebSocketCallback):
    """
    Shift a team member down
    """

    REQUEST_TYPE = TeamMemberRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.team_index
        game, player_model = get_request_context(hydrated)
        state: "State" = game.state
        player: Player = state.get_player_by_id(player_model.id)
        if idx >= len(player.team) - 1:
            return ReportingResponse(success=False, message="Pokemon is already at bottom")
        player.team[idx], player.team[idx + 1] = player.team[idx + 1], player.team[idx]
        return ReportingResponse(success=True)


class RemoveFromTeam(WebSocketCallback):
    """
    Remove a member from a team
    """

    REQUEST_TYPE = TeamMemberRequest

    @staticmethod
    def callback(hydrated: "BaseModel"):
        idx = hydrated.team_index
        game, player_model = get_request_context(hydrated)
        state: "State" = game.state
        player: Player = state.get_player_by_id(player_model.id)
        if idx not in range(len(player.team)):
            return ReportingResponse(success=False, message="Invalid request")
        player.remove_from_team(idx)
        return ReportingResponse(success=True)


class PartyRequest(WebSocketPlayerRequest):
    """
    Operates on a Party Pokemon

    Operations:
    * add to team
    * move to storage
    """

    party_index: int


class AddToTeam(WebSocketCallback):

    REQUEST_TYPE = PartyRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.party_index
        game, player_model = get_request_context(hydrated)
        state: "State" = game.state
        player: Player = state.get_player_by_id(player_model.id)
        if idx > PARTY_SIZE:
            return ReportingResponse(success=False, message="Invalid request")
        player.add_party_to_team(idx)
        return ReportingResponse(success=True)


class UpdatePartyConfigRequest(WebSocketPlayerRequest):
    """
    Change the party config for a player
    """

    party_config: PartyConfig


class UpdatePartyConfig(WebSocketCallback):

    REQUEST_TYPE = UpdatePartyConfigRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)
        party_config: PartyConfig = hydrated.party_config
        player.party_config = party_config
        print(f'Updated party config for {player} to {party_config}')
        return ReportingResponse(success=True)


class MoveToStorage(WebSocketCallback):

    REQUEST_TYPE = PartyRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.party_index
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)
        player.move_party_to_storage(player.party[idx])
        return ReportingResponse(success=True)


class ReleaseFromParty(WebSocketCallback):

    REQUEST_TYPE = PartyRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.party_index
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)
        player_manager: PlayerManager = game.player_manager
        player_party = player_manager.player_party(player)
        player_manager.release_pokemon(player, player_party[idx])
        return ReportingResponse(success=True)


# STORAGE APIs

class StorageRequest(WebSocketPlayerRequest):
    """
    Interact with a Pokemon in storage
    """

    storage_index: int


class MoveToParty(WebSocketCallback):

    REQUEST_TYPE = StorageRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.storage_index
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)
        player.move_storage_to_party(player.storage[idx])
        return ReportingResponse(success=True)


class ReleaseFromStorage(WebSocketCallback):

    REQUEST_TYPE = StorageRequest

    @staticmethod
    def callback(hydrated: BaseModel):
        idx = hydrated.storage_index
        game, player_model = get_request_context(hydrated)
        player: Player = game.state.get_player_by_id(player_model.id)
        player_manager: PlayerManager = game.player_manager
        party = player_manager.player_party(player)
        player_manager.release_pokemon(player, party[idx])
        return ReportingResponse(success=True)


# ITEM AND ITEM EVENT APIs


# NOTE: this should be at the bottom to do dynamic evaluation
API_REQUEST_CLASSES = [
    x for x in globals().values() if isinstance(x, type) and issubclass(x, WebSocketCallback)
]

DISPATCHER = {x.__name__: x.callback for x in API_REQUEST_CLASSES if x is not None}


def get_request_endpoint_by_name(name):
    """
    Do a lookup by API model and return a class type to make a message out of
    """
    for api in API_REQUEST_CLASSES:
        if api.__name__ == name:
            return api
    raise TypeError(f"Could not identify an API of type {name}")
