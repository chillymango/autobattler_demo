"""
Why the fuck isn't shiny logic working jfc
"""
import unittest
from engine.env import Environment
from engine.models.association import PlayerShop, associate, dissociate
from engine.models.enums import PokemonId
from engine.models.player import Player
from engine.models.shop import ShopOffer
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory
from engine.shop import ShopManager


class TestShinyLogic(unittest.TestCase):
    """
    blahhhh
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='Balbsbert Bang')
        self.env.add_player(self.p1)
        self.env.initialize()

    def test_shiny_logic(self):
        """
        make a shiny poke
        """
        pm: PlayerManager = self.env.player_manager
        sm: ShopManager = self.env.shop_manager
        # give three of the same pokemon and then run shiny checker
        pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        sm.check_shiny(self.p1, 'pikachu')
        pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        sm.check_shiny(self.p1, 'pikachu')
        pm.create_and_give_pokemon_to_player(self.p1, 'pikachu')
        sm.check_shiny(self.p1, 'pikachu')

    def test_shiny_through_shop(self):
        """
        Test catching through shop
        """
        # create a fake shop
        shop = [
            ShopOffer(pokemon=PokemonId.pikachu),
            ShopOffer(pokemon=PokemonId.pikachu),
            ShopOffer(pokemon=PokemonId.pikachu),
            ShopOffer(pokemon=PokemonId.pikachu),
            ShopOffer(pokemon=PokemonId.pikachu)
        ]

        for card in self.env.state.shop_window.get(self.p1, []):
            if card is not None:
                dissociate(PlayerShop, self.p1, card)

        for rolled in shop:
            associate(PlayerShop, self.p1, rolled)
        self.env.state.load_containers()

        sm: ShopManager = self.env.shop_manager
        sm.catch(self.p1, 0)
        sm.catch(self.p1, 1)
        sm.catch(self.p1, 2)
        import IPython; IPython.embed()


if __name__ == "__main__":
    unittest.main()
