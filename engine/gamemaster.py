"""
Data Attribute Dictionary for the Pokemon Go gamemaster.json
"""
import json
from multiprocessing.sharedctypes import Value
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

    def get_lvl_cpm(self, lvl: float) -> float:
        """
        Get the CP multiplier for a level
        """
        index = int((lvl - 1) * 2.0)
        return self.cpms[index]

    def get_pokemon_stats(self, pokemon_name: str, stats: Stats):
        """
        Get stats for a Pokemon.

        Only supports ATK, DEF, HP for now.
        """
        if stats not in (Stats.ATK, Stats.DEF, Stats.HP):
            raise ValueError(f"Unsupported base stat {stats}")

        for spec in self.gamemaster_dict['pokemon']:
            if spec['speciesId'] == pokemon_name:
                stat_key = stats.name.lower()
                return spec['baseStats'][stat_key]

        print(f"Could not find {stats.name} for {pokemon_name}")


    def __getattr__(self, attr: str):
        return getattr(self.gamemaster, attr)
