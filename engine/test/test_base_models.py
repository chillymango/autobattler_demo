"""
Make some test models.

Verify garbage collection and query behavior works properly.
"""
import sys
import unittest
from enum import Enum
from engine.models.base import Entity


class TestGCEntity(Entity):

    test_public: str


class TestOtherEntity(Entity):

    anattr: int


class PlayerArchetype(Enum):
    ROCK_SOLID = 0
    ROCKET_SOLID = 1  # lmao
    CLAIRVOYANT = 2


class TestPlayerEntity(Entity):
    """
    Fake player with some fake attrs to match on for testing
    """

    name: str
    archetype: PlayerArchetype


class TestBaseModels(unittest.TestCase):
    """
    yadda
    """

    ENTITY_CLASSES = [
        TestGCEntity,
        TestOtherEntity,
    ]

    def test_garbage_collection(self):
        test = TestGCEntity(test_public='hahaha')
        test2 = TestOtherEntity(anattr=3)
        self.assertEqual(sys.getrefcount(test), 2)
        self.assertEqual(sys.getrefcount(test2), 2)
        del test
        # TODO: how do i actually test this lol

    def test_no_cross_talk(self):
        """
        No counts in the other pool

        Shouldn't be a problem anymore since adding metaclass queryable
        """
        test = TestGCEntity(test_public='oh shit waddup')
        test2 = TestOtherEntity(anattr=10)
        self.assertEqual(len(TestGCEntity.all()), 1)
        self.assertEqual(len(TestOtherEntity.all()), 1)

    def test_filter_by_attribute(self):
        test = TestPlayerEntity(name='Schmitty Werbenjagermanjensen', archetype=PlayerArchetype.ROCK_SOLID)
        test2 = TestPlayerEntity(name='He was Number One', archetype=PlayerArchetype.ROCKET_SOLID)
        test3 = TestPlayerEntity(name='clair', archetype=PlayerArchetype.CLAIRVOYANT)
        matches = TestPlayerEntity.all(name='Schmitty Werbenjagermanjensen')
        self.assertEqual(matches[0], test)
        self.assertEqual(len(matches), 1)

    def tearDown(self):
        """
        Delete all created objects of all testing types
        """
        for entityclass in self.ENTITY_CLASSES:
            for entity in entityclass.query():
                entity.delete()
        super().tearDown()


if __name__ == "__main__":
    unittest.main()
