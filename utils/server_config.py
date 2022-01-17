"""
Load the server configuration
"""
import json
from pydantic import BaseModel

DEFAULT_PATH = "server_config.json"


class ServerConfig(BaseModel):
    """
    Game server configuration information
    """

    bind: str

    @classmethod
    def parse_filepath(cls, path=DEFAULT_PATH):
        return super().parse_file(path)

    @property
    def websocket_path(self):
        """
        Path to the game websocket
        """
        return f"{self.bind.replace('http://', 'ws://')}/game_buttons"

    @property
    def pubsub_path(self):
        """
        Path to the pubsub endpoint
        """
        return f"{self.bind.replace('http://', 'ws://')}/pubsub"

    @property
    def lobby_pubsub_path(self):
        """
        Path to the lobby pubsub endpoint
        """
        return f"{self.bind.replace('http://', 'ws://')}/lobby_pubsub"
