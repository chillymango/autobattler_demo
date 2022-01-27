"""
Base Component Definition

Game runs in an update loop

Start Turn
* execute `step_turn`
** this should update the component for the current turn
"""
import json
import typing as T
import weakref
from uuid import UUID

from utils.serialize import default_serialize
from utils.strings import camel_case_to_snake_case

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.models.state import State

_T = T.TypeVar("_T")


class Component:
    """
    Template class for adding new game components.

    These game components will have actions in the game and turn loop.

    The default action will be no-op.

    TODO: split components into things that run on turn phase updates and things that just
    contain game logic. Compounding them together right now is pretty unfortunate.

    NOTE: for associative relationships, the component that manages the primary model will manage
    the relationships for that model.
    Example: in the player-pokemon one-to-many association, the player is the primary (one), and
    the Pokemon is the joined (many). This means that the player manager is the component that
    should be responsible for managing player Pokemon.
    """

    ENV_PROXY = None

    @property
    def dependencies(self) -> T.List:
        """
        TODO: implement this to make components declare components that this one depends on
        """
        return []

    def __init__(self, env: "Environment", state: "State"):
        self.env = weakref.proxy(env)
        self.state = state  # TODO: this probably memory leaks
        classname = self.__class__.__name__
        snakecase = camel_case_to_snake_case(classname)
        # make it a weakref so ref count doesn't increment and the env can be garbage collected
        setattr(self.env, snakecase, weakref.proxy(self))
        if self.ENV_PROXY is not None:
            # also set a weakref here
            setattr(self.env, self.ENV_PROXY, weakref.proxy(self))

        self.log = self.env.log

    def to_dict(self):
        """
        Return a dict representation (key-value mapping) of the component.

        By default will return a dictionary with only the name of the component in it.
        """
        return {"name": self.__class__.__name__}

    def initialize(self):
        pass

    # server game execution actions
    # local game env should not attempt to run these
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
