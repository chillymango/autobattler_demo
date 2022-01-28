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


def extract_from_container_by_id(container, _id):
    """
    Get a matching entity from a container by entity ID
    """
    if _id is None:
        return None

    for x in container:
        if getattr(x, 'id', None) == _id:
            return x
    return None
