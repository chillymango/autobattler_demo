"""
"""
from engine.models.base import Entity
from engine.models.enums import PokemonId


class ShopOffer(Entity):
    """
    Represents a Pokemon shop entry
    """

    pokemon: PokemonId
    consumed: bool = False
