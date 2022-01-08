"""
Game state should be stored here or something
"""
import time
import typing as T
from enum import Enum
from engine.base import Component
from engine.battle_seq import BattleManager
from engine.match import CreepRoundManager
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player
from engine.player import PlayerManager
from engine.pokemon import PokemonFactory
from engine.pokemon import TmManager
from engine.shop import ShopManager
from engine.turn import Turn


class GamePhase(Enum):
    """
    Enumeration of game phases

    INITIALIZATION: setup the game
    TURN_SETUP: all game components should run turn setup actions
    TURN_PREP: enable user input and feed UI event loop callbacks into components
    TURN_EXECUTE: lock user input and run component execute actions
    TURN_CLEANUP: keep user input locked, report status here, prepare for next turn
    CLEANUP: final cleanup of all components, should enter the COMPLETED phase
    COMPLETED: issued when the game is over and all actors should cease all actions.
    ERROR: transition here when something goes wrong. No outward transitions.
    """

    INITIALIZATION = 0
    TURN_SETUP = 1
    TURN_DECLARE_TEAM = 2
    TURN_PREPARE_TEAM = 3
    TURN_PREP = 4
    TURN_EXECUTE = 5
    TURN_CLEANUP = 6
    CLEANUP = 7
    COMPLETED = 8
    ERROR = 9


class GameState:
    """
    Overarching object that covers all game data.

    Probably want to put stuff here that will load state from pubsub messages when doing
    the multiplayer form of the game.
    """

    @property
    def component_classes(self):
        return [
            Turn,
            PlayerManager,
            TmManager,
            PokemonFactory,
            Matchmaker,
            CreepRoundManager,
            ShopManager,
            BattleManager,
        ]

    def __init__(self, players: T.List[Player]):
        self.phase = GamePhase.INITIALIZATION
        self.players = players
        self.components: T.List[Component] = []
        self.stage_duration = None
        self.time_to_next_stage = None

        self.current_player = self.players[0]

        for component in self.component_classes:
            self.components.append(component(self))

    def start_game(self):
        """
        Step from INITIALIZE into first TURN_SETUP
        """
        if not self.phase == GamePhase.INITIALIZATION:
            raise RuntimeError("Attempted to start game while in non-initialize")
        self.phase = GamePhase.TURN_SETUP

    def step_loop(self):
        """
        Step forward one phase in the main turn loop.
        """
        if self.phase == GamePhase.TURN_SETUP:
            # run turn setup actions
            for component in self.components:
                component.turn_setup()
            self.phase = GamePhase.TURN_DECLARE_TEAM
            return
        if self.phase == GamePhase.TURN_DECLARE_TEAM:
            # this is just a UI phase, don't do anything
            if self.time_to_next_stage is None:
                self.time_to_next_stage = 30.0
                self.stage_duration = 30.0
            elif self.time_to_next_stage < 0.0:
                self.time_to_next_stage = None
                self.phase = GamePhase.TURN_PREPARE_TEAM
            else:
                self.time_to_next_stage -= 0.2
                time.sleep(0.2)
            return
        if self.phase == GamePhase.TURN_PREPARE_TEAM:
            # this is just a UI phase, don't do anything
            if self.time_to_next_stage is None:
                self.time_to_next_stage = 30.0
                self.stage_duration = 30.0
            elif self.time_to_next_stage < 0.0:
                self.time_to_next_stage = None
                self.phase = GamePhase.TURN_EXECUTE
            else:
                self.time_to_next_stage -= 0.2
                time.sleep(0.2)
            return
        if self.phase == GamePhase.TURN_EXECUTE:
            for component in self.components:
                component.turn_execute()
            self.phase = GamePhase.TURN_CLEANUP
            return
        if self.phase == GamePhase.TURN_CLEANUP:
            for component in self.components:
                component.turn_cleanup()
            # TODO: this probably blocks, fix with event loop
            if self.time_to_next_stage is None:
                self.time_to_next_stage = 10.0
                self.stage_duration = 10.0
            elif self.time_to_next_stage < 0.0:
                self.time_to_next_stage = None
                self.phase = GamePhase.TURN_SETUP
            else:
                self.time_to_next_stage -= 0.2
                time.sleep(0.2)
            return

        raise RuntimeError("Game phase not in main turn loop yet")


if __name__ == "__main__":
    # simple unit test
    humans = [
        Player('Ashe Ketchum', type_=EntityType.HUMAN),
        Player('Red Dawn', type_=EntityType.HUMAN),
        Player('Blue Steel', type_=EntityType.HUMAN),
        Player('Yellow Fever', type_=EntityType.HUMAN),
        Player('Gold Digger', type_=EntityType.HUMAN),
        Player('Crystal Meth', type_=EntityType.HUMAN),
    ]
    computers = [
        Player('Skynet'),
        Player('HAL')
    ]
    players = humans + computers
    state = GameState(players)

    import IPython; IPython.embed()
