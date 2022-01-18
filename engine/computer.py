from engine.base import Component


class ComputerLogic:
    """
    Here's what the computer is thinking or how it comes up with its moves
    """


class AIManager(Component):
    """
    Logic for running computers goes in here
    """

    def turn_setup(self):
        """
        At this stage, the computer, during setup, will read something about the game state
        and use that to inform the decisions it makes during purchasing
        """
