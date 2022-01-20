"""
Setup a test environment and create items
"""
import unittest
from engine.env import Environment
from engine.items import ItemManager
from engine.models.player import Player
from engine.pokemon import EvolutionManager, PokemonFactory
from engine.models.items import PersistentPokemonItem
from engine.models.items import PersistentPlayerItem
from engine.models.items import InstantPokemonItem
from engine.models.items import InstantPlayerItem
from engine.models.pokemon import Pokemon

class TestEnvironment(Environment):

    @property
    def component_classes(self):
        return [
            ItemManager,
            PokemonFactory,
            EvolutionManager,
        ]


class TestInstantPokemonItem(InstantPokemonItem):
    """
    Test function is to cause a Pokemon to evolve immediately
    """

    @classmethod
    def test_factory_method(cls, env):
        return cls(env, name='Test Pokemon Evo Stone')

    def can_use(self):
        return isinstance(self.holder, Pokemon)

    def use(self):
        evo: EvolutionManager = self._env.evolution_manager
        evo.evolve(self.holder)


class TestPersistentPokemonItem(PersistentPokemonItem):
    """
    Test function is to give a pokemon 100 XP every turn setup
    """

    @classmethod
    def test_factory_method(cls, env):
        return cls(env, name='Test Pokemon XP Trinket')

    def can_use(self):
        return isinstance(self.holder, Pokemon)

    def turn_setup(self):
        self.holder: Pokemon
        self.holder.xp += 100


class TestInstantPlayerItem(InstantPlayerItem):
    """
    Test function is to give a player 5 master balls on use
    """

    @classmethod
    def test_factory_method(cls, env):
        return cls(env, name='Test Master Ball')

    def can_use(self):
        return isinstance(self.holder, Player)

    def use(self):
        self.holder: Player
        self.holder.master_balls += 5


class TestPersistentPlayerItem(PersistentPlayerItem):
    """
    Test function is to give a player a flute charge every turn
    """

    @classmethod
    def test_factory_method(cls, env: Environment):
        return cls(env, name='Test Poke Flute')

    def can_use(self):
        return isinstance(self.holder, Player)

    def turn_setup(self):
        self.holder: Player
        self.holder.flute_charges += 1


class TestItemManager(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = TestEnvironment(8)
        self.env.initialize()

        # create a test factory and inject it
        im: ItemManager = self.env.item_manager
        im.import_factory(
            PersistentPlayerItem,
            dict(test_poke_flute=TestPersistentPlayerItem.test_factory_method)
        )
        im.import_factory(
            InstantPlayerItem,
            dict(test_master_ball=TestInstantPlayerItem.test_factory_method)
        )
        im.import_factory(
            PersistentPokemonItem,
            dict(test_xp_trinket=TestPersistentPokemonItem.test_factory_method)
        )
        im.import_factory(
            InstantPokemonItem,
            dict(test_evo_stone=TestInstantPokemonItem.test_factory_method)
        )

    def test_item_creation(self):
        item_manager: ItemManager = self.env.item_manager
        item_manager.create_item("test_poke_flute")
        item_manager.create_item("test_master_ball")
        item_manager.create_item("test_evo_stone")
        item_manager.create_item("test_xp_trinket")

        with self.assertRaises(Exception):
            item_manager.create_item("fuckin garbage")

    def test_item_usage_valid_targets(self):
        """
        Provide valid item targets
        """
        player = Player(name='balbert bang')
        poke_factory: PokemonFactory = self.env.pokemon_factory
        poke = poke_factory.create_pokemon_by_name('pikachu')
        item_manager: ItemManager = self.env.item_manager

        test_flute: PersistentPlayerItem = item_manager.create_item("test_poke_flute")
        test_flute.holder = player
        test_flute.turn_setup()
        self.assertEqual(player.flute_charges, 1)

        test_master_ball: InstantPlayerItem = item_manager.create_item("test_master_ball")
        test_master_ball.holder = player
        test_master_ball.immediate_action()
        self.assertEqual(player.master_balls, 5)

        test_xp_trinket: PersistentPokemonItem = item_manager.create_item("test_xp_trinket")
        test_xp_trinket.holder = poke
        test_xp_trinket.turn_setup()
        self.assertEqual(poke.xp, 100)

        test_evo_stone: InstantPokemonItem = item_manager.create_item("test_evo_stone")
        test_evo_stone.holder = poke
        test_evo_stone.immediate_action()
        self.assertEqual(poke.name, "raichu")


if __name__ == "__main__":
    unittest.main()
