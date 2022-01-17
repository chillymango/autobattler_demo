import time
import typing as T
import weakref
from collections import defaultdict
from queue import Queue
from pydantic import BaseModel
from pydantic import Field
from engine.player import Player

from datetime import datetime
from collections import namedtuple
from engine.base import Component

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.state import State


__ALL_PLAYERS__ = "__ALL_PLAYERS_CONSTANT__"


class Message(BaseModel):

    msg: str
    time: float = Field(default_factory=time.time)


class Logger:
    """
    Primarily meant to log messages to the user and NOT for actual system logging.

    Messages are stored in queue objects here. When the pubsub channels are set up, the
    messages will be published to all subscribers.
    """

    def __init__(self, env: "Environment", state: "State"):
        """
        Duplicate most of the component setup but skip the log hooks
        """
        self.env = weakref.proxy(env)
        self.state = state  # TODO: this probably memory leaks
        #self.message_player_queue = {player: Queue() for player in self.state.players}
        self.message_player_queue = defaultdict(lambda: Queue())
        self.message_global_queue = Queue()

    def log(self, msg: str, recipient: T.Union[T.List[Player], Player]=__ALL_PLAYERS__):
        print('Using Logger log')
        message = Message(msg=msg)
        print(message)
        if recipient == __ALL_PLAYERS__:
            self.message_global_queue.put(message)
            return
        if isinstance(recipient, Player):
            recipient = [recipient]
        for player in recipient:
            self.message_player_queue[player].put(message)
