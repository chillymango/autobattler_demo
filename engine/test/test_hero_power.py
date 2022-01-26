"""
Setup a test environment for hero powers
"""
import typing as T
import unittest

from engine.env import Environment
from engine.items import ItemManager
from engine.models.player import Player
from engine.pokemon import EvolutionManager, PokemonFactory
from engine.models.items import InstantPokemonItem
from engine.models.items import PlayerHeroPower
from engine.models.pokemon import Pokemon
from engine.player import PlayerManager


class TestInstantPokemonItem(InstantPokemonItem):
    """
    Test function is to change a pokemon's primary type
    """

    @classmethod
    def test_factory_method(cls, env):
        return cls(env, name='Test Dragon Scale')

    def can_use(self):
        return isinstance(self.holder, Pokemon)

    def use(self):
        if not isinstance(self.holder, Pokemon):
            return
        if self.holder.is_type('dragon'):
            return

        self.holder.battle_card.poke_type1 = 'dragon' 






class TestHeroPower(PlayerHeroPower):
    """
    Test function to use lance's hero power
    """
    success: bool = False
    hp_cost: int = 2

    @classmethod
    def test_factory_method(cls, env):
        return cls(env, name='Test Lance Fetish')

    def use(self, player: "Player" = None):
        """
        get a dragon scale item 
        """
        if player.balls > self.hp_cost :
            player_manager: PlayerManager = self._env.player_manager
            player_manager.create_and_give_item_to_player(player, "test_dragon_scale")
            self.success = True

TEST_FACTORIES: T.Dict[T.Type, T.Dict[str, T.Callable]] = {
    InstantPokemonItem: dict(test_dragon_scale=TestInstantPokemonItem.test_factory_method),
    PlayerHeroPower: dict(test_lance_fetish=TestHeroPower.test_factory_method)
}


class TestItemManager(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(8)
        self.env.initialize()

        # create a test factory and inject it
        im: ItemManager = self.env.item_manager
        for itemtype, factory in TEST_FACTORIES.items():
            im.import_factory(itemtype, factory)

    def test_item_usage_valid_targets(self):
        """
        Provide valid item targets
        """
        player = Player(name='balbert bang')
        poke_factory: PokemonFactory = self.env.pokemon_factory
        poke = poke_factory.create_pokemon_by_name('pikachu')
        item_manager: ItemManager = self.env.item_manager
        test_hp: PlayerHeroPower = item_manager.create_item("test_lance_fetish")
        test_hp.holder = player
        player.balls = 5

        test_hp.use(player)
        state = self.env.state
        print(state.player_inventory)
        player_inventory_names = set(item.name for item in state.player_inventory[player.name])
        self.assertTrue("Test Dragon Scale" in player_inventory_names)

        dragon_scale = state.player_inventory[player][0]
        dragon_scale.holder = poke
        dragon_scale.use(poke)
        self.assertEqual(poke.battle_card.poke_type1, "dragon")
        self.assertTrue(player.balls == 3)

        test_hp.use(player)
        state = self.env.state
        player_inventory_names = set(item.name for item in state.player_inventory[player.name])
        self.assertFalse("Test Dragon Scale" in player_inventory_names)


if __name__ == "__main__":
    unittest.main()
