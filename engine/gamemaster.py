"""
Data Attribute Dictionary for the Pokemon Go gamemaster.json
"""
import json
from munch import DefaultMunch

from engine.base import Component
from engine.models.items import Stats


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

    def get_pokemon_stats(self, pokemon_name: str, stats: Stats, level: float):
        """
        Get stats for a Pokemon.

        Only supports ATK, DEF, HP for now.
        """
        import IPython; IPython.embed()


    def __getattr__(self, attr: str):
        return getattr(self.gamemaster, attr)
