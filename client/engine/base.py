"""
Base Component Definition

Game runs in an update loop

Start Turn
* execute `step_turn`
** this should update the component for the current turn
"""
import typing as T

from utils.string import camel_case_to_snake_case

if T.TYPE_CHECKING:
    from engine.state import GameState


class GuiArray:
    """
    Base class that will signal some flags whenever it's updated.
    """


class Component:
    """
    Template class for adding new game components.

    These game components will have actions in the game and turn loop.

    The default action will be no-op.
    """

    def __init__(self, state: "GameState"):
        self.state = state
        self.initialize()
        classname = self.__class__.__name__
        snakecase = camel_case_to_snake_case(classname)
        setattr(self.state, snakecase, self)

    def initialize(self):
        pass

    def turn_setup(self):
        """
        Turn Setup Phase Actions

        This is the phase where the game will compute actions to setup the current turn
        before allowing the player to input actions.
        """
        pass

    def turn_prep(self):
        """
        Turn Prep Phase Actions

        This is the phase where the game will allow user input to prepare for battle.
        """
        pass

    def turn_execute(self):
        """
        Turn Execute Phase Actions

        This is the phase where the game will run combat.
        """
        pass

    def turn_cleanup(self):
        """
        Turn Cleanup Phase Actions

        This is where combat results will be presented and a short period will be allowed
        for additional user input.
        """
        pass

    def cleanup(self):
        """
        Cleanup Phase Actions

        When the game is ready to clean up, process actions here.
        """
        pass
