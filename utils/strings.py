"""
String utils
"""
from functools import reduce
from posixpath import split
from uuid import uuid4


def camel_case_to_snake_case(camel):
    """
    Convert a CamelCase into a snake_case
    """
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, camel).lower()


def crunch_spaces(string: str):
    """
    If a space is surrounded by two capital letters, remove the space.

    This is just a hack to render things like H_P into HP
    """
    base = ''
    for idx in range(len(string) - 2):
        if string[idx + 1] in ('_', ' ') and string[idx].isupper() and string[idx + 2].isupper():
            continue
        base += string[idx]
    return base + string[-1]


def uuid_as_str():
    """
    Default constructor
    """
    return str(uuid4())


def split_half_on_space(instr):
    """
    Find the space closest to the middle and turn it into a newline.
    """
    words = instr.split(' ')
    first = ''
    for idx, word in enumerate(words):
        first += word
        if len(first) > len(instr) / 2:
            break
    else:
        return instr

    return ' '.join(words[:idx]) + '\n' + ' '.join(words[idx:])
