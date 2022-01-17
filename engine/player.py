"""
Player Object Model
"""
import typing as T

from engine.base import Component
from engine.models.player import Player


class PlayerManager(Component):
    """
    Keeps track of players from turn to turn
    """

    def initialize(self):
        self.players: T.List[Player] = self.state.players
        for player in self.players:
            player.is_alive = True
            player.hitpoints = 20
            player.balls = 5

    def turn_setup(self):
        """
        Add balls, run special events before prep phase
        """
        # base update
        # TODO: make this scale as the game goes on
        for player in self.players:
            player.balls += 5
            player.energy += 5

    def turn_cleanup(self):
        """
        Check if any player has health at 0 or less. If so, mark them as dead.
        """
        for player in self.players:
            if player.hitpoints <= 0:
                player.is_alive = False
