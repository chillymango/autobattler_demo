"""
Client loads a stripped down env to help with rendering results
"""
from engine.env import Environment
from engine.match import Matchmaker
from engine.models.state import State
from engine.pokemon import PokemonFactory
from engine.shop import ShopManager
from engine.sprites import SpriteManager


class ClientState(State):
    """
    Do not load associative containers

    ...
    and probably some other shit
    """

    def load_containers(self):
        """
        Do not load from associations

        Use the provided ID mappings to map objects
        """
        return


class ClientEnvironment(Environment):

    @property
    def default_component_classes(self):
        return [
            Matchmaker,
            PokemonFactory,
            ShopManager,
            SpriteManager,
        ]

    @property
    def state_factory(self):
        return ClientState.default

    def initialize(self):
        """
        Do not modify the phase
        """
        for component in self.components:
            component.initialize()
