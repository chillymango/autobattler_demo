"""
"""
from engine.models.base import Entity


class ShopOffer(Entity):
    """
    Represents a Pokemon shop entry
    """

    pokemon: str
