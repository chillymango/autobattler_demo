"""
Pokemon Object Representation
"""
from uuid import uuid4


class Pokemon:
    """
    Instantiate unique object based on name
    """

    def __init__(self, pokemon_name, id=None):
        self.name = pokemon_name
        self.id = id or uuid4()
