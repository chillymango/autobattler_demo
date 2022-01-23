"""
Player Object Model
"""
import typing as T

from engine.base import Component
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.items import ItemManager


class PlayerManager(Component):
    """
    Keeps track of players from turn to turn
    """

    def initialize(self):
        self.players: T.List[Player] = self.state.players
        for player in self.players:
            player.is_alive = True
            player.hitpoints = 20
            player.balls = 10

    def get_pokemon_holder(self, pokemon: Pokemon) -> T.Optional[Player]:
        """
        Get the player that currently holds a Pokemon
        """
        for player in self.players:
            if pokemon in player.roster:
                return player

    def turn_setup(self):
        """
        Add balls, run special events before prep phase
        """
        # base update
        # TODO: make this scale as the game goes on
        for player in self.players:
            player.balls += 7
            player.energy += 2

    def turn_cleanup(self):
        """
        Check if any player has health at 0 or less. If so, mark them as dead.
        """
        for player in self.players:
            if player.hitpoints <= 0:
                self.log("You have died!", recipient=player)
                player.is_alive = False