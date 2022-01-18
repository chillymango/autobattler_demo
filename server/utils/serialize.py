"""
Object serialization helpers
"""
import json
from enum import Enum
from uuid import UUID


def default_serialize(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise ValueError("No idea how to serialize {}".format(obj))


if __name__ == "__main__":

    class TestClass:
        """
        HERE WE GO AGAINNNN
        """
        def __init__(self):
            self.attr = 0

    thing = TestClass()
    thing2 = TestClass()
    thing.nested = thing2
    thing.nested2 = ['lol', 'ok', 'seriously', TestClass(), {1: TestClass()}, thing]

    # this will recurse, should probably fix...
    default_serialize(thing)
