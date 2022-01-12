"""
Client loads a stripped down env to help with rendering results
"""
from engine.env import Environment
from engine.logger import Logger
from engine.match import Matchmaker
from engine.sprites import SpriteManager


class ClientEnvironment(Environment):

    @property
    def component_classes(self):
        return [
            Logger,  # probably not needed but just in case
            Matchmaker,
            SpriteManager,
        ]

    def initialize(self):
        """
        Do not modify the phase
        """
        for component in self.components:
            component.initialize()
