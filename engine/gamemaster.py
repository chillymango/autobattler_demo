"""
Data Attribute Dictionary for the Pokemon Go gamemaster.json
"""
import json
from munch import DefaultMunch

from engine.base import Component


class GameMaster(Component):
    """
    Load gamemaster as JSON and support lookup with attributes
    """

    ENV_PROXY = 'gm'
    GAMEMASTER_PATH = 'battle_engine/src/data/gamemaster.json'

    def initialize(self):
        super().initialize()
        with open(self.GAMEMASTER_PATH, 'r') as gamemaster_json:
            self.gamemaster_dict = json.load(gamemaster_json)
        self.gamemaster = DefaultMunch.fromDict(self.gamemaster_dict)

    def __getattr__(self, attr: str):
        return getattr(self.gamemaster, attr)
