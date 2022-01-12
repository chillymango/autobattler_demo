"""
UI Button Click Interactions

e.g roll shop, catch pokemon, change team, etc

TODO: eventually use websockets
"""
import typing as T
from fastapi import APIRouter
from pydantic import BaseModel

from server.api.base import ReportingResponse
from server.api.base import PlayerContextRequest
from server.api.lobby import get_request_context

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.player import Player
    from engine.shop import ShopManager
    from engine.state import State

shop_router = APIRouter(prefix="/shop")


@shop_router.post("/roll", response_model=ReportingResponse)
async def api_roll_shop(request: PlayerContextRequest):
    """
    Roll the shop for a player if possible.
    """
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player = state.get_player_by_id(player_model.id)

    shop_manager: ShopManager = game.shop_manager
    shop_manager.roll(player)


class CatchPokemonRequest(PlayerContextRequest):

    shop_index: int


@shop_router.post("/catch", response_model=ReportingResponse)
async def api_catch(request: CatchPokemonRequest):
    """
    Catch the Pokemon at a specific index in the shop of a player
    """
    game, player_model = get_request_context(request)
    player: Player = game.state.get_player_by_id(player_model.id)

    shop_manager: ShopManager = game.shop_manager
    shop_manager.catch(player, request.shop_index)
