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
    from engine.state import State


class GuiArray:
    """
    Base class that will signal some flags whenever it's updated.
    """


_T = T.TypeVar("_T")


class _Synchronized:
    """
    Template class for an object whose data needs to be synchronized over the web.

    These objects typically represent game env which must be common between clients, or
    shared from server to client.

    This object should provide encode / decode methods for transfer over the wire.

    TODO: use BaseModel from pydantic why am i so dumb
    """

    def encode(self):
        """
        Encode object into JSON representation
        """
        return json.dumps(self.__dict__, default=default_serialize)

    @classmethod
    def from_dict(cls, dict_repr):
        """
        Generate an object from a dictionary representation.
        """
        raise NotImplementedError

    @classmethod
    def decode(cls: T.Type[_T], data) -> _T:
        """
        Decode object from JSON string
        """
        return cls.from_dict(json.loads(data))

    def update(self, dict_repr):
        """
        Update this object with dictionary data values.

        TODO: probably do this eventually when data amounts get large
        """


class Component:
    """
    Template class for adding new game components.

    These game components will have actions in the game and turn loop.

    The default action will be no-op.
    """

    def __init__(self, env: "Environment", state: "State"):
        self.env = weakref.proxy(env)
        self.state = state  # TODO: this probably memory leaks
        classname = self.__class__.__name__
        snakecase = camel_case_to_snake_case(classname)
        # make it a weakref so ref count doesn't increment and the env can be garbage collected
        setattr(self.env, snakecase, weakref.proxy(self))

        # do something here with pubsub channels

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