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

from utils.strings import camel_case_to_snake_case

if T.TYPE_CHECKING:
    from server.engine.env import Environment


class GuiArray:
    """
    Base class that will signal some flags whenever it's updated.
    """


class _Synchronized:
    """
    Template class for an object whose data needs to be synchronized over the web.

    These objects typically represent game state which must be common between clients, or
    shared from server to client.

    This object should provide encode / decode methods for transfer over the wire.
    """

    def to_dict(self):
        """
        Dictionary representation of this object.

        If this is defined and returns a dictionary, will be used to encode the object.
        """
        return None

    def encode(self):
        """
        Encode object into JSON representation
        """
        dict_repr = self.to_dict()
        if dict_repr:
            return json.dumps(dict_repr)

        raise NotImplementedError

    @classmethod
    def from_dict(cls, dict_repr):
        """
        Generate an object from a dictionary representation.

        If any keys are left over and unused, a warning will be raised.
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, data):
        """
        Decode object from JSON string
        """
        return cls.from_dict(json.loads(data))


class Component:
    """
    Template class for adding new game components.

    These game components will have actions in the game and turn loop.

    The default action will be no-op.
    """

    def __init__(self, state: "Environment"):
        self.state = weakref.proxy(state)
        self.initialize()
        classname = self.__class__.__name__
        snakecase = camel_case_to_snake_case(classname)
        # make it a weakref so ref count doesn't increment and the state can be garbage collected
        setattr(self.state, snakecase, weakref.proxy(self))

    def to_dict(self):
        """
        Return a dict representation (key-value mapping) of the component.

        By default will return a dictionary with only the name of the component in it.
        """
        return {"name": self.__class__.__name__}

    def initialize(self):
        pass

    # server game execution actions
    # local game state should not attempt to run these
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
