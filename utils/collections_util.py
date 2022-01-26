"""
Helppp
"""


def pad_list_to_length(inlist, length, pad=None):
    """
    Performs operation in-place
    """
    if len(inlist) >= length:
        return

    inlist += [pad] * (length - len(inlist))
