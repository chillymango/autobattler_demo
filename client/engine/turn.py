from collections import namedtuple

from engine.base import Component

StageConfig = namedtuple("StageConfig", ["stage", "round", "location"])


class Turn(Component):
    """
    Keeps track of turn and stage
    """

    CONFIG_PATH = 'engine/data/stages.txt'

    def advance(self):
        self._number += 1
        self._stage = self.stages[self._number]

    def retract(self):
        if self._number > 0:
            self._number -= 1
        else:
            raise ValueError("Cannot go beyond turn 0")

    @property
    def stage(self):
        return self._stage

    @property
    def number(self):
        return self._number

    def initialize(self):
        self._number = 0
        self._stage = None
        with open(self.CONFIG_PATH, 'r') as stages_file:
            stages_raw = stages_file.readlines()

        self.stages = {}
        turn_number = 1
        for line in stages_raw:
            # turn is unit indexed
            if not line:
                continue
            if line.startswith('#'):
                continue

            entries = line.split()
            stage = int(entries[0])
            round = int(entries[1])
            location = ' '.join(entries[2:])
            self.stages[turn_number] = StageConfig(stage, round, location)
            turn_number += 1

    def turn_setup(self):
        self.advance()

    def __repr__(self):
        return "Turn {}".format(self._number)

    def get_stage_for_turn(self, turn_number):
        """
        Given a turn number, get the relevant StageConfig tuple
        """
        return self.stages[turn_number]
