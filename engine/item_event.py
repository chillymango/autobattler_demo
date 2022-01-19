from engine.base import Component


class ItemEventManager(Component):
    """
    Defines and manages the item distribution
    """

    def initialize(self):
        """
        Load data files which define item distribution schedules
        """
