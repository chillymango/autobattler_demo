from datetime import datetime
from collections import namedtuple
from engine.base import Component


class Message:

    def __init__(self, msg, time=None):
        self.msg = msg
        self.time = time or datetime.now()

    def __str__(self):
        return "{}: {}".format(self.time.ctime(), self.msg)


class Logger(Component):
    """
    Primarily meant to log messages to the user and NOT for actual system logging.
    """

    DEBUG = False
    TIMESTAMPS = False

    def initialize(self):
        super().initialize()
        self.messages = []

    def clear(self):
        self.messages = []
        self.log("Cleared logger history")

    def log(self, msg):
        self.messages.append(Message(msg))
        if self.DEBUG:
            print(str(Message(msg)))

    def debug(self, msg):
        print(str(Message(msg)))

    @property
    def content(self):
        if self.TIMESTAMPS:
            return '\n'.join([str(msg) for msg in self.messages])
        return '\n'.join([x.msg for x in self.messages])
