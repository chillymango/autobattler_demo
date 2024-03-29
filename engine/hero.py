"""
Hero Power
"""
import typing as T
from random import randint
from random import sample
from engine.base import Component
from engine.models.hero import NORMAL_HEROES
from engine.models.hero import Hero
from engine.models.hero import PRISMATIC_HEROES
from engine.models.player import Player


class HeroManager(Component):
    """
    Responsible for initially assigning hero powers to players.
    """

    ENV_PROXY = "hero"

    def initialize(self):
        """
        TODO: make this a player choice instead of a random assignment
        """
        super().initialize()
        if randint(0, 4) == 4:
            print('HOLY SHIT PRISMATIC HEROES TIME!!!')
            HEROES = PRISMATIC_HEROES
        else:
            HEROES = NORMAL_HEROES

        heroes = [x for x in HEROES]
        for player in self.state.players:
            self.state.player_hero[str(player.id)] = hero = sample(heroes, 1)[0]
            print(f'Assigned hero {hero} to {player}')
            heroes.remove(hero)
            hero.set_env(self.env)
            if hasattr(hero._power, 'StartOfGame'):
                hero._power.StartOfGame(player=player)

    def get_player_hero(self, player: Player) -> Hero:
        return self.state.player_hero[player.id]

    def use_hero_power(self, player: Player) -> None:
        """
        Use a Player hero power
        """
        try:
            hero = self.get_player_hero(player)
            hero._power.immediate_action(player)
            return True
        except Exception as exc:
            print(repr(exc))
            return False

    def turn_execute(self):
        super().turn_execute()
