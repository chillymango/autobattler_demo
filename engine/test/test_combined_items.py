"""
Give some combat items to some Pokemon and watch the item effects
"""
import unittest

from engine.env import Environment
from engine.models.player import Player
from engine.player import PlayerManager


class TestCombatItems(unittest.TestCase):
    """
    smhhh
    """

    def setUp(self):
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='Fat Ass')
        self.p2 = Player(name='Fuck Ass')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.initialize()
        self.pm: PlayerManager = self.env.player_manager

    def test_assault_vest(self):
        return
        pika = self.pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        assault_vest = self.pm.create_and_give_item_to_player(self.p1, 'AssaultVest')
        self.pm.give_item_to_pokemon(pika, assault_vest)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_cell_battery(self):
        pika = self.pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        cell_battery = self.pm.create_and_give_item_to_player(self.p1, 'CellBattery')
        cell_battery.level = 3  # need to manually set if not combining
        self.pm.give_item_to_pokemon(pika, cell_battery)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_focus_band(self):
        eevee = self.pm.create_and_give_pokemon_to_player(self.p1, 'magikarp')
        focus_band = self.pm.create_and_give_item_to_player(self.p1, 'FocusBand')
        focus_band.level = 3  # need to manually set if not combining
        self.pm.give_item_to_pokemon(eevee, focus_band)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()
