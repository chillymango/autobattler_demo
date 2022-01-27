"""
Holy shit this sucks

Pydantic gets into a nested recursion infinite loop in encoding if there are
recursive type fields.

Example:

class A(BaseModel):
    attr: B

class B(BaseModel):
    attr: A

This will have bad things happen...

This test will test our example solution and make sure all classes that we define this
interaction for do not do stupid things.
"""
import unittest
from pydantic import BaseModel
from pydantic import Field
from engine.env import Environment
from engine.inventory import PlayerInventoryManager
from engine.items import ItemManager
from engine.models.base import Entity
from engine.models.player import Player
from engine.pokemon import PokemonFactory


class TestA(Entity):
    """
    Internal / branch node
    """

    child: "TestB" = None


class TestB(Entity):
    """
    Leaf node / referred entity
    """

    parent: "TestA" = Field(exclude=True, default=None)

TestA.update_forward_refs()
TestB.update_forward_refs()


class TestRecursiveBase(unittest.TestCase):
    """
    Test Recursive Definitions
    """

    def test_example_json_encode(self):
        a = TestA()
        b = TestB()
        a.child = b
        b.parent = a


class TestRecursiveGameModels(unittest.TestCase):
    """
    Test real game model recursive definitions
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(2)
        self.p1 = Player(name='Albert Yang')
        self.env.add_player(self.p1)
        self.env.initialize()

    def test_pokemon_player(self):
        # nested game definition
        poke_factory: PokemonFactory = self.env.pokemon_factory
        poke1 = poke_factory.create_pokemon_by_name('pikachu')
        self.p1.add_to_party(poke1)
        self.p1.json()

    def test_item_player(self):
        # nested item definition
        inventory_manager: PlayerInventoryManager = self.env.inventory_manager
        item = inventory_manager.create_and_give_item_to_player("master_ball", self.p1)
        import IPython; IPython.embed()
        self.p1.json()


if __name__ == "__main__":
    unittest.main()
