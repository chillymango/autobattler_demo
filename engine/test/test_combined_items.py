"""
Give some combat items to some Pokemon and watch the item effects
"""
import sys
import unittest
import typing as T
from contextlib import redirect_stdout
from engine.battle import BattleManager

from engine.env import Environment
from engine.models.association import PlayerInventory, PlayerRoster
from engine.models.items import Item
from engine.models.player import Player
from engine.models.pokemon import Pokemon
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

    def teardown(self):
        # remove all pokemon and items
        for inv in PlayerInventory.all():
            inv.delete()
        for ros in PlayerRoster.all():
            ros.delete()
        for poke in Pokemon.all():
            poke.delete()
        for item in Item.all():
            item.delete()

    def run_round_1_test_and_log_results(self, output_path: str):
        """
        Run a round 1 fight

        Log results to a file.
        """
        with open(output_path, 'w+') as output:
            with redirect_stdout(output):
                # TODO(albert): make this fuckin work
                pass

    def test_assault_vest(self):
        pika = self.pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        assault_vest = self.pm.create_and_give_item_to_player(self.p1, 'AssaultVest')
        assault_vest.level = 3
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
        eevee = self.pm.create_and_give_pokemon_to_player(self.p1, 'eevee')
        focus_band = self.pm.create_and_give_item_to_player(self.p1, 'FocusBand')
        focus_band.level = 3  # need to manually set if not combining
        self.pm.give_item_to_pokemon(eevee, focus_band)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_choice_specs(self):
        blastoise = self.pm.create_and_give_pokemon_to_player(self.p1, 'blastoise')
        choice_specs = self.pm.create_and_give_item_to_player(self.p1, 'ChoiceSpecs')
        choice_specs.level = 2
        self.pm.give_item_to_pokemon(blastoise, choice_specs)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_life_orb(self):
        dratini = self.pm.create_and_give_pokemon_to_player(self.p1, "dratini")
        life_orb = self.pm.create_and_give_item_to_player(self.p1, 'LifeOrb')
        life_orb.level = 3
        self.pm.give_item_to_pokemon(dratini, life_orb)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_quick_powder(self):
        weedle = self.pm.create_and_give_pokemon_to_player(self.p1, 'weedle')
        quick_powder = self.pm.create_and_give_item_to_player(self.p1, 'QuickPowder')
        quick_powder.level = 30  # set to insane to see it work
        self.pm.give_item_to_pokemon(weedle, quick_powder)
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()

    def test_expert_belt(self):
        machoke = self.pm.create_and_give_pokemon_to_player(self.p1, 'machoke')
        expert_belt = self.pm.create_and_give_item_to_player(self.p1, 'ExpertBelt')
        expert_belt.level = 100  # set it to something insane to verify effect
        self.pm.give_item_to_pokemon(machoke, expert_belt)

        # poor chansey...
        chansey = self.pm.create_and_give_pokemon_to_player(self.p2, 'chansey')
        battle_manager: BattleManager = self.env.battle_manager
        res = battle_manager.battle(self.p1, self.p2)
        print('\n'.join([repr(x) for x in res['events']]))
        print(res['render'])

    def test_frozen_heart(self):
        spearow = self.pm.create_and_give_pokemon_to_player(self.p1, 'spearow')
        frozen_heart = self.pm.create_and_give_item_to_player(self.p1, 'FrozenHeart')
        frozen_heart.level = 30  # make it super obvious
        self.pm.give_item_to_pokemon(spearow, frozen_heart)

        # cool em off
        for component in self.env.components:
            component.turn_setup()
        for component in self.env.components:
            component.turn_execute()
