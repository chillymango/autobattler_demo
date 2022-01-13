from server.api.base import PlayerContextRequest


class GameWindow:
    """
    Helper Mixin

    Supports player context generation
    """

    env = None
    player = None

    def get_player_context(self):
        return PlayerContextRequest(player=self.player, game_id=self.env.id)
