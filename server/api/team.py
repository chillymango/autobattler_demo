"""
Team Interaction API

TODO: use websockets
"""
import typing as T
from fastapi import APIRouter
from engine.models.player import TEAM_SIZE

from server.api.base import ReportingResponse
from server.api.base import PlayerContextRequest
from server.api.lobby import get_request_context

if T.TYPE_CHECKING:
    from engine.player import Player
    from engine.models.state import State

team_router = APIRouter(prefix="/team")

PARTY_SIZE = 6


class ShiftRequest(PlayerContextRequest):
    """
    Depending on if submitted to the UP or DOWN API, will either shift a pokemon
    up or down in the battle order for a team.
    """

    index: int


@team_router.post("/shift_up", response_model=ReportingResponse)
async def api_shift_upward(request: ShiftRequest):
    idx = request.index
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player: Player = state.get_player_by_id(player_model.id)
    if idx < 1:
        return ReportingResponse(success=False, message="Pokemon is already at top")
    player.team[idx], player.team[idx - 1] = player.team[idx - 1], player.team[idx]
    return ReportingResponse(success=True)


@team_router.post("/shift_down", response_model=ReportingResponse)
async def api_shift_downward(request: ShiftRequest):
    idx = request.index
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player: Player = state.get_player_by_id(player_model.id)
    if idx > len(player.team) - 1:
        return ReportingResponse(success=False, message="Pokemon is already at bottom")
    player.team[idx], player.team[idx + 1] = player.team[idx + 1], player.team[idx]
    return ReportingResponse(success=True)


class AddToTeamRequest(PlayerContextRequest):

    party_idx: int


@team_router.post("/add", response_model=ReportingResponse)
async def api_add_to_team(request: AddToTeamRequest):
    """
    Issue request to add a Pokemon to team

    Will only work if the Pokemon is already a member of the party
    """
    idx = request.party_idx
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player: Player = state.get_player_by_id(player_model.id)
    if idx > PARTY_SIZE:
        return ReportingResponse(success=False, message="Invalid request")
    player.add_party_to_team(idx)
    return ReportingResponse(success=True)


class RemoveFromTeamRequest(PlayerContextRequest):

    team_idx: int


@team_router.post("/remove", response_model=ReportingResponse)
async def api_remove_from_team(request: RemoveFromTeamRequest):
    """
    Issue request to remove from team
    """
    idx = request.team_idx
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player: Player = state.get_player_by_id(player_model.id)
    if idx not in range(len(player.team)):
        return ReportingResponse(success=False, message="Invalid request")
    player.remove_from_team(idx)
    return ReportingResponse(success=True)
