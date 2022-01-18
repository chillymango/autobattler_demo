"""
Client loads a stripped down env to help with rendering results
"""
from engine.env import Environment
from engine.match import Matchmaker
from engine.pokemon import PokemonFactory
from engine.shop import ShopManager
from engine.sprites import SpriteManager


class ClientEnvironment(Environment):

    @property
    def component_classes(self):
        return [
            Matchmaker,
            PokemonFactory,
            ShopManager,
            SpriteManager,
        ]

    def initialize(self):
        """
        Do not modify the phase
        """
        for component in self.components:
            component.initialize()
