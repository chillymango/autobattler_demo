"""
Support the debug window buttons

this module should really be named cheatcodes
"""
import typing as T
from fastapi import APIRouter
from fastapi import WebSocket
from pydantic import BaseModel

from server.api.base import ReportingResponse
from server.api.base import PlayerContextRequest
from server.api.lobby import PlayerContext, get_request_context
from engine.models.phase import GamePhase

if T.TYPE_CHECKING:
    from engine.battle import BattleManager
    from engine.match import Matchmaker
    from engine.models.state import State
    from engine.turn import Turn

debug_router = APIRouter(prefix="/debug")


@debug_router.post("/new_matches", response_model=ReportingResponse)
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
    state.current_matches = matchmaker.organize_round()
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


@debug_router.post("/initiate_battle", response_model=ReportingResponse)
def api_initiate_battle(request: PlayerContextRequest):
    """
    Initiate a battle
    """
    game, _ = get_request_context(request)
    battle_manager: BattleManager = game.battle_manager
    battle_manager.turn_execute()
    return ReportingResponse(success=True)


@debug_router.post("/pause_game", response_model=ReportingResponse)
def api_debug_pause(request: PlayerContextRequest):
    """
    Pause the game
    """
    game, _ = get_request_context(request)
    game.paused = True
    return ReportingResponse(success=True)


@debug_router.post("/unpause_game", response_model=ReportingResponse)
def api_debug_unpause(request: PlayerContextRequest):
    """
    Unpause the game
    """
    game, _ = get_request_context(request)
    game.paused = False
    return ReportingResponse(success=True)


class DumpStateRequest(PlayerContextRequest):
    
    dump_all: bool = True


@debug_router.post("/dump_state", response_model=State)
def api_dump_state(request: DumpStateRequest):
    game, player = get_request_context(request)
    if request.dump_all:
        return game.state
    else:
        return game.state.for_player(player)
