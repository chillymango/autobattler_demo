"""
String utils
"""
from functools import reduce


def camel_case_to_snake_case(camel):
    """
    Convert a CamelCase into a snake_case
    """
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, camel).lower()
