"""
Base API class abstraction

TODO: look into using fastapi-utils for cbv. For now just define everything explicitly.
"""
from fastapi.routing import APIRouter
from pydantic import BaseModel

from server.api.player import Player
from utils.context import GameContext


class GameNotFound(Exception):
    """
    Raise when a game cannot be found
    """


class ReportingResponse(BaseModel):
    """
    Basic response which has a `success` flag and a `message` field to report status
    """

    success: bool
    message: str = ""


class PlayerContextRequest(BaseModel):
    """
    A request that includes a player and a game as part of the context
    """

    player: Player
    game_id: str

    @classmethod
    def from_game_context(cls, ctx: GameContext, **kwargs):
        return cls(player=ctx.player, game_id=str(ctx.game.id), **kwargs)


class MethodView:

    # by default requests have no attrs
    REQUEST_TYPE = BaseModel
    RESPONSE_TYPE = BaseModel

    def __init__(self, endpoint: str,router: APIRouter, methods=["GET"]):
        self.endpoint = endpoint
        self.router = router

        self.methods = methods
        if self.supports_get:
            router.add_api_route(endpoint, self.get)
        if self.supports_post:
            router.add_api_route(endpoint, self.post)

        router.add_api_route(endpoint, )

    @property
    def supports_get(self):
        return "GET" in self.methods

    @property
    def supports_post(self):
        return "POST" in self.methods

    def get(self):
        pass

    def post(self):
        """
        Business logic
        """
        raise NotImplementedError
