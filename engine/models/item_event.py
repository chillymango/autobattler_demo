from pydantic import BaseModel


# what defines an item event?
# random item events could be:
#  guaranteed item
#  set of items with a different distribution

class ItemEvent(BaseModel):
    """
    Defines an event where a player gets an item randomly, or is given a choice of items.
    """


class GivenItemEvent(ItemEvent):
    """
    This is an event where a player is given a random item
    """
