"""
combine items, check associations, validity, etc
"""
import unittest
from engine.env import Environment
from engine.items import ItemManager
from engine.models import items
from engine.models.association import PlayerInventory
from engine.models.association import PokemonHeldItem
from engine.models.player import Player
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory


class TestItemCombos(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='po go')
        self.env.add_player(self.p1)
        self.env.initialize()

    def test_item_combos(self):
        im: ItemManager = self.env.item_manager
        atk_large_1 = im.create_item('LargeAttackShard')
        atk_large_2 = im.create_item('LargeAttackShard')
        combo_atk_large = im.combine_items(atk_large_1, atk_large_2)
        self.assertTrue(isinstance(combo_atk_large, items.LifeOrb))
        self.assertEqual(combo_atk_large.level, 3)

        spd_small_1 = im.create_item('SmallSpeedShard')
        spd_large_1 = im.create_item('LargeSpeedShard')
        combo_spd_med = im.combine_items(spd_small_1, spd_large_1)
        self.assertTrue(isinstance(combo_spd_med, items.Metronome))
        self.assertEqual(combo_spd_med.level, 2)

    def test_item_combo_player_assignment(self):
        """
        Test the cases with Pokemon and player associations
        """
        state = self.env.state
        pm: PlayerManager = self.env.player_manager
        shard1 = pm.create_and_give_item_to_player(self.p1, "LargeDefenseShard")
        shard2 = pm.create_and_give_item_to_player(self.p1, "LargeEnergyShard")
        pm.combine_player_items(self.p1, shard1, shard2)

    def test_give_item_to_pokemon(self):
        pm: PlayerManager = self.env.player_manager
        pika = pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        shard1 = pm.create_and_give_item_to_player(self.p1, "SmallHitPointShard")
        pm.give_item_to_pokemon(pika, shard1)
        shard2 = pm.create_and_give_item_to_player(self.p1, "LargeAttackShard")
        pm.combine_player_items(self.p1, shard1, shard2)
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
