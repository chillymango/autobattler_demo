import json
import unittest

from engine.models.containers import PokemonStorage
from engine.models.containers import PokemonParty
from engine.models.player import EntityType
from engine.models.player import Player
from engine.models.pokemon import Pokemon
from engine.env import Environment
from engine.pokemon import PokemonFactory


class TestStorageEnv(Environment):
    """
    Override components that get loaded
    """

    @property
    def component_classes(self):
        return [
            PokemonFactory
        ]


class TestContainers(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = TestStorageEnv(8)
        self.env.pokemon_factory.initialize()
        self.pokemon_factory: PokemonFactory = self.env.pokemon_factory
        self.player = Player(name='Albert Yang', type=EntityType.HUMAN)
        self.test_pokemon = dict(
            pikachu=self.pokemon_factory.create_pokemon_by_name('pikachu'),
            raichu=self.pokemon_factory.create_pokemon_by_name('raichu'),
            mewtwo=self.pokemon_factory.create_pokemon_by_name('mewtwo'),
            rhydon=self.pokemon_factory.create_pokemon_by_name('rhydon')
        )

    def test_pokemon_storage(self):
        """
        Pokemon storage is an ordered, dynamically sized mutable sequence
        """
        # create a container, add some pokemon, and verify that they all get player set
        container = PokemonStorage(self.player, 2)
        pika = self.test_pokemon['pikachu']
        rai = self.test_pokemon['raichu']
        mewtwo = self.test_pokemon['mewtwo']
        container.append(pika)
        container.append(rai)
        self.assertEqual(pika.player, self.player)
        self.assertEqual(rai.player, self.player)

        # try to add a third and verify it fails
        with self.assertRaises(ValueError):
            container.append(mewtwo)

        # then remove the pokemon from the container and verify the container unsets
        container.remove(pika)
        self.assertIsNone(pika.player)
        container.remove(rai)
        self.assertIsNone(rai.player)

    def test_pokemon_party(self):
        party = PokemonParty(self.player, 3)
        pika = self.test_pokemon['pikachu']
        rai = self.test_pokemon['raichu']
        mewtwo = self.test_pokemon['mewtwo']
        ryry = self.test_pokemon['rhydon']
        party.append(pika)
        self.assertEqual(pika.player, self.player)
        self.assertListEqual(party.list, [pika, None, None])
        party.append(rai)
        self.assertEqual(rai.player, self.player)
        self.assertListEqual(party.list, [pika, rai, None])
        party.append(mewtwo)
        self.assertEqual(mewtwo.player, self.player)
        self.assertListEqual(party.list, [pika, rai, mewtwo])
        # test max size
        with self.assertRaises(Exception):
            party.append(ryry)
        self.assertIsNone(ryry.player)
        # remove and make sure the ordering stays the same
        party.remove(rai)
        self.assertIsNone(rai.player)
        self.assertListEqual(party.list, [pika, None, mewtwo])

    def test_json_encode(self):
        """
        Try and create a Player object with inventories, then test encode/decode
        """
        pika = self.test_pokemon['pikachu']
        self.player.add_to_party(pika)
        output_dict = self.player.json()
        res = json.loads(output_dict)['party'][0]
        poke = Pokemon.parse_obj(res)
        self.assertEqual(poke, pika)


if __name__ == "__main__":
    unittest.main()
