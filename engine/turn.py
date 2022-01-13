from pydantic.main import BaseModel

from engine.base import Component

class StageConfig(BaseModel):
    stage: int
    round: int
    location: str = ""


class Turn(Component):
    """
    Keeps track of turn and stage
    """

    CONFIG_PATH = 'data/stages.txt'

    def advance(self):
        self.state.turn_number += 1
        self.state.stage = self.stages[self.state.turn_number]

    def retract(self):
        if self.state.turn_number > 0:
            self.state.turn_number -= 1
            self.state.stage = self.stages[self.state.turn_number]
        else:
            print("Cannot go beyond turn 0")

    @property
    def stage(self):
        """
        refers to the stage number
        """
        return self.state.stage.stage

    @property
    def number(self):
        return self.state.turn_number

    def initialize(self):

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
            self.stages[turn_number] = StageConfig(stage=stage, round=round, location=location)
            turn_number += 1

    def turn_setup(self):
        self.advance()

    def __repr__(self):
        return "Turn {}".format(self.state.turn_number)

    def get_stage_for_turn(self, turn_number):
        """
        Given a turn number, get the relevant StageConfig tuple
        """
        return self.stages[turn_number]
