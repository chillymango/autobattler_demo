"""
Make some association models and verify they work
"""
import unittest
import weakref

from engine.env import Environment
from engine.items import ItemManager
from engine.models.player import Player

from engine.models.association import Association
from engine.models.association import AssociatedContainer
from engine.models.association import PlayerInventoryAssociation
from engine.models.association import get_associations_for_entity
from engine.models.state import State


class TestAssociationModel(unittest.TestCase):
    """
    Make some players / inventory and create associations between them and do lookups

    Also do a speed test or something? Not sure how that would work...
    """

    def setUp(self):
        super().setUp()
        self.env = Environment.create_webless_game(4)
        self.p1 = Player(name='Ashe')
        self.p2 = Player(name='Brock')
        self.p3 = Player(name='Misty')
        self.env.add_player(self.p1)
        self.env.add_player(self.p2)
        self.env.add_player(self.p3)
        self.env.initialize()

    def test_associations(self):
        # create items, give them to players (manually)
        item_manager: ItemManager = self.env.item_manager
        item = item_manager.create_item("master_ball")
        item2 = item_manager.create_item("poke_flute")

        # create association
        association = PlayerInventoryAssociation(entity1=item, entity2=self.p1)
        association2 = PlayerInventoryAssociation(entity1=item2, entity2=self.p1)
        container = AssociatedContainer(
            PlayerInventoryAssociation,
            container_class=set,
            reference_entity=self.p1
        )
        self.assertEqual(len(container.container), 2)

        # test the encoding?
        container.json()

        # see if creating an object gets instantly garbage collected or not idk
        item3 = item_manager.create_item("fire_stone")
        PlayerInventoryAssociation(entity1=item3, entity2=self.p1)
        # TODO: they don't look like they get collected (maybe won't happen until OOM)

    def test_state_encode(self):
        """
        Put these associations in state?
        """
        state: State = self.env.state
        container = AssociatedContainer(
            PlayerInventoryAssociation,
            container_class=set,
            reference_entity=self.p1
        )
        # instantiate...
        container.container
        state.player_inventory_raw[self.p1.id] = container.container
        item_manager: ItemManager = self.env.item_manager
        item = item_manager.create_item("master_ball")
        item2 = item_manager.create_item("poke_flute")

        # create association
        association = PlayerInventoryAssociation(entity1=item, entity2=self.p1)
        association2 = PlayerInventoryAssociation(entity1=item2, entity2=self.p1)
        import IPython; IPython.embed()

    def test_sandbox(self):
        pass
        


if __name__ == "__main__":
    unittest.main()
