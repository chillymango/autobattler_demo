from asyncqt import asyncSlot
from server.api.base import PlayerContextRequest


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

    def get_player_context(self):
        return PlayerContextRequest(player=self.player, game_id=self.env.id)
