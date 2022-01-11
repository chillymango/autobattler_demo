"""
Game state should be stored here or something
"""
import time
import typing as T
from enum import Enum
from uuid import uuid4

from engine.base import Component
from engine.battle_seq import BattleManager
from engine.logger import Logger
from engine.match import CreepRoundManager
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player
from engine.player import PlayerManager
from engine.pokemon import EvolutionManager, PokemonFactory
from engine.pokemon import TmManager
from engine.shop import ShopManager
# sprite manager not used in web
#from engine.sprites import SpriteManager
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
    TURN_COMPLETE = 7
    CLEANUP = 8
    COMPLETED = 9
    ERROR = 10


# i need some class here that contains only the raw information about the game and its state
# and does not include things like factories
# this split needs to happen now so i can make the state be fully transmitted over the wire

# maybe we just do a `mutate` function or something


class Environment:
    """
    TODO: rename this to Environment
    and create a `State` object that's actually just game data

    Overarching object that covers all game data.

    Probably want to put stuff here that will load state from pubsub messages when doing
    the multiplayer form of the game.
    """

    @property
    def component_classes(self):
        return [
            Logger,  # this always has to go first -- TODO: fix this shit
            Turn,
            PlayerManager,
            # sprite manager not used in web
            #SpriteManager,
            TmManager,
            PokemonFactory,
            Matchmaker,
            CreepRoundManager,
            ShopManager,
            BattleManager,
            EvolutionManager,
        ]

    def to_json(self):
        """
        this is either galaxy brain or smooth brain but
        what if we could dump this into a JSON object by just looking at all the attributes

        logic:
        traverse all attributes of `Environment`.
        If it's a numeric value, record it.
        If it's a subclass of `Component`, keep traversing to get a JSON.
        """

    def __init__(self, max_players: int):
        self._id = uuid4()
        print("Created env with id {}".format(id))
        self.phase = GamePhase.INITIALIZATION
        self.max_players = max_players
        self.players = []
        self.components: T.List[Component] = []
        self.stage_duration = None
        self.time_to_next_stage = None

        if self.players:
            self.current_player = self.players[0]
        else:
            self.current_player = None

        for component in self.component_classes:
            self.components.append(component(self))

    def __del__(self):
        print('Deleting env with id {}'.format(self._id))

    def add_player(self, player):
        if len(self.players) >= self.max_players:
            raise ValueError("Player count {} already reached".format(self.max_players))
        self.players.append(player)

    def remove_player(self, player):
        if player not in self.players:
            raise ValueError("Player {} not in game players".format(player))
        self.players.remove(player)

    @property
    def id(self):
        return self._id

    @property
    def is_finished(self):
        return self.phase in [GamePhase.COMPLETED, GamePhase.ERROR]

    @property
    def is_running(self):
        return self.phase not in [GamePhase.INITIALIZATION, GamePhase.ERROR, GamePhase.COMPLETED]

    def start_game(self):
        """
        Step from INITIALIZE into first TURN_SETUP
        """
        if not self.phase == GamePhase.INITIALIZATION:
            raise RuntimeError("Attempted to start game while in non-initialize")
        self.logger.log("Starting game")
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
                self.time_to_next_stage = 15.0
                self.stage_duration = 15.0
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
                self.time_to_next_stage = 15.0
                self.stage_duration = 15.0
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
            self.phase = GamePhase.TURN_COMPLETE
        if self.phase == GamePhase.TURN_COMPLETE:
            # TODO: this probably blocks, fix with event loop
            if self.time_to_next_stage is None:
                self.time_to_next_stage = 5.0
                self.stage_duration = 5.0
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
    state = Environment(players)

    import IPython; IPython.embed()
