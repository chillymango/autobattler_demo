import typing as T
from qasync import asyncSlot
from server.api.base import PlayerContextRequest

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.models.player import Player
    from engine.models.state import State
    from server.api.user import User


class AsyncCallback:
    """
    This sucks ass
    TODO: make this work though because the asyncSlot() doesn't work with
    dynamically generated functions
    """

    def __init__(self, method, *args):
        self.method = method
        self.args = args

    #@asyncSlot()
    async def __call__(self, *_):
        # NOTE: the first arg to this is some boolean???
        print(self.args)
        coro = asyncSlot()(self.method(*self.args))
        print(coro)
        return await coro


class GameWindow:
    """
    Helper Mixin

    Supports player context generation
    """

    env = None
    player = None

    def __init__(
        self,
        env: "Environment" = None,
        user: "User" = None,
    ):
        self.env = env
        self.user = user

    @property
    def render_methods(self):
        """
        Returns a list of the methods used to render the window
        """
        return []

    def get_player_context(self):
        return PlayerContextRequest(player=self.player, game_id=self.env.id)
