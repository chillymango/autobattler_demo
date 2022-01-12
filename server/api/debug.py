"""
Support the debug window buttons

this module should really be named cheatcodes
"""
import typing as T
from fastapi import APIRouter
from pydantic import BaseModel

from engine.state import GamePhase
from server.api.base import ReportingResponse
from server.api.base import PlayerContextRequest
from server.api.lobby import get_request_context

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.match import Matchmaker
    from engine.player import Player
    from engine.shop import ShopManager
    from engine.state import State
    from engine.turn import Turn

debug_router = APIRouter(prefix="/debug")


@debug_router.post("/start_game", response_model=ReportingResponse)
def api_make_new_matches(request: PlayerContextRequest):
    """
    Request the Matchmaker create new matches
    """
    game, _ = get_request_context(request)
    state: "State" = game.state
    matchmaker: "Matchmaker" = game.matchmaker

    # these rounds were not played so do not commit them to memory
    if state.phase == GamePhase.TURN_EXECUTE:
        return ReportingResponse(success=False, message="matches are currently playing")
    state.matches = matchmaker.organize_round()
    return ReportingResponse(success=True)


@debug_router.post("/add_energy", response_model=ReportingResponse)
def api_add_energy(request: PlayerContextRequest):
    """
    Add 100 energy
    """
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player = state.get_player_by_id(player_model.id)
    player.energy += 100
    return ReportingResponse(success=True)


@debug_router.post("/add_pokeballs", response_model=ReportingResponse)
def api_add_pokeballs(request: PlayerContextRequest):
    """
    Add 100 pokeballs
    """
    game, player_model = get_request_context(request)
    state: "State" = game.state
    player = state.get_player_by_id(player_model.id)
    player.balls += 100
    return ReportingResponse(success=True)


@debug_router.post("/advance_turn", response_model=ReportingResponse)
def api_advance_turn(request: PlayerContextRequest):
    """
    Advance turn by 1
    """
    game, _ = get_request_context(request)
    turn: "Turn" = game.turn
    turn.advance()
    return ReportingResponse(success=True)


@debug_router.post("/retract_turn", response_model=ReportingResponse)
def api_retract_turn(request: PlayerContextRequest):
    """
    Retract turn by 1
    """
    game, _ = get_request_context(request)
    turn: "Turn" = game.turn
    turn.retract()
    return ReportingResponse(success=True)
