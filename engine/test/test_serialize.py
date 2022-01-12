"""
Test encoding / decoding on state objects
"""
import unittest

from pydantic import BaseModel
from engine.env import Environment
from engine.player import EntityType, Player
from engine.pokemon import BattleCard, Pokemon, PokemonFactory
from engine.state import State


class TestEncodeDecode(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.env = Environment(4)

        self.player1 = Player(name='test player', type=EntityType.HUMAN)
        self.player2 = Player(name='someone else')
        self.env.add_player(self.player1)
        self.env.add_player(self.player2)
        self.state: State = self.env.state
        self.factory = PokemonFactory(self.env, self.state)
        self.factory.initialize()

        # create fixtured objects
        self.pokemon = self.factory.create_pokemon_by_name("pikachu")
        self.battle_card = self.pokemon.battle_card

    def _test_encode_decode_encode_cycle(self, obj: BaseModel):
        """
        Test that encoding -> decoding -> re-encoding gives the same dict.

        This suggests that the encode-decode cycle is idempotent on data values.
        """
        encoded = obj.json()
        decoded = obj.parse_raw(encoded)
        self.assertEqual(decoded.json(), encoded)

    def test_player(self):
        """
        Verify the player object can be encoded / decoded
        """
        self._test_encode_decode_encode_cycle(self.player1)

    def test_battle_card(self):
        self._test_encode_decode_encode_cycle(self.battle_card)

    def test_pokemon(self):
        self._test_encode_decode_encode_cycle(self.pokemon)

    def test_state(self):
        self.state.shop_window_raw = {player.id: [None] * 6 for player in self.state.players}
        self._test_encode_decode_encode_cycle(self.state)


if __name__ == "__main__":
    unittest.main()
