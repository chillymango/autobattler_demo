from engine.base import Component


class Turn(Component):
    """
    Keeps track of turn
    """

    def advance(self):
        self._number += 1

    def retract(self):
        if self._number > 0:
            self._number -= 1
        else:
            raise ValueError("Cannot go beyond turn 0")

    @property
    def number(self):
        return self._number

    def initialize(self):
        self._number = 0

    def turn_setup(self):
        self.advance()

    def __repr__(self):
        return "Turn {}".format(self._number)
