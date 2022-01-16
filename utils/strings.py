"""
String utils
"""
from functools import reduce
from uuid import uuid4


def camel_case_to_snake_case(camel):
    """
    Convert a CamelCase into a snake_case
    """
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, camel).lower()


def uuid_as_str():
    """
    Default constructor
    """
    return str(uuid4())
