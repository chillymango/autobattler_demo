"""
Gamemaster dict
"""
import json
from munch import DefaultMunch

from engine.models.enums import Move, PokemonId
from engine.models.stats import Stats


DEFAULT_PATH = 'battle_engine/src/data/gamemaster.json'

class GameMaster:
    """
    Load gamemaster as JSON and support lookup with attributes
    """

    ENV_PROXY = 'gm'
    GAMEMASTER_PATH = 'battle_engine/src/data/gamemaster.json'

    def __init__(self):
        with open(self.GAMEMASTER_PATH, 'r') as gamemaster_json:
            self.gamemaster_dict = json.load(gamemaster_json)
        self.gamemaster = DefaultMunch.fromDict(self.gamemaster_dict)

        # build a mapping of pokemon ID to spec
        self.pokemon_spec = {}
        for spec in self.gamemaster_dict['pokemon']:
            self.pokemon_spec[PokemonId[spec['speciesId']]] = spec

    def get_lvl_cpm(self, lvl: float) -> float:
        """
        Get the CP multiplier for a level
        """
        index = int((lvl - 1) * 2.0)
        return self.cpms[index]

    def get_default_pokemon_stats(self, pokemon: PokemonId):
        """
        Get all default stats for a Pokemon
        """
        for spec in self.gamemaster_dict['pokemon']:
            if spec['speciesId'] == pokemon.name:
                return spec

    def get_default_move_stats(self, move: Move):
        """
        Get all default stats for a Move
        """
        for spec in self.gamemaster_dict['moves']:
            if spec['moveId'] == move.name:
                return spec

    def __getattr__(self, attr: str):
        return getattr(self.gamemaster, attr)

    def get_nickname(self, pokemon: PokemonId):
        """
        Get the default nickname for a Pokemon
        """
        return self.pokemon_spec[pokemon]['speciesName']


gamemaster = GameMaster()
