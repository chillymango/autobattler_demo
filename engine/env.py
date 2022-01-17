"""
Game env should be stored here or something
"""
import time
import typing as T
from uuid import UUID
from uuid import uuid4

from engine.base import Component
from engine.battle_seq import BattleManager
from engine.logger import __ALL_PLAYERS__
from engine.logger import Logger
from engine.match import CreepRoundManager
from engine.match import Matchmaker
from engine.player import PlayerManager
from engine.pokemon import EvolutionManager, PokemonFactory
from engine.pokemon import TmManager
from engine.pubsub import PubSubInterface
from engine.shop import ShopManager
from engine.models.state import State
from engine.turn import Turn
from utils.phase import GamePhase


class Environment:
    """
    TODO: rename this to Environment
    and create a `env` object that's actually just game data

    Overarching object that covers all game data.

    Probably want to put stuff here that will load env from pubsub messages when doing
    the multiplayer form of the game.
    """

    @property
    def component_classes(self):
        return [
            #Logger,  # this always has to go first -- TODO: fix this shit
            Turn,
            PlayerManager,
            TmManager,
            PokemonFactory,
            Matchmaker,
            CreepRoundManager,
            ShopManager,
            BattleManager,
            EvolutionManager,
            PubSubInterface,  # this should probably go last
        ]

    def __init__(self, max_players: int, id=None):
        self._id = UUID(id) if id else uuid4()
        print("Created env with id {}".format(self._id))
        self.state: State = State.default()
        self.state.phase = GamePhase.INITIALIZATION
        self.max_players = max_players
        self.components: T.List[Component] = []
        self.logger = Logger(env=self, state=self.state)

        # uh i don't think we actually use this anymore
        self.current_player = None

        for component in self.component_classes:
            self.components.append(component(self, self.state))

    def log(self, msg: str, recipient=__ALL_PLAYERS__):
        """
        Stand-in until replaced by the Logger component
        """
        self.logger.log(msg, recipient=recipient)

    def __del__(self):
        print('Deleting env with id {}'.format(self._id))

    def add_player(self, player):
        if len(self.state.players) >= self.max_players:
            raise ValueError("Player count {} already reached".format(self.max_players))
        if player in self.state.players:
            print("Player {} already in players".format(player))
        self.state.players.append(player)

    def remove_player_by_id(self, player_id):
        for player in self.state.players:
            if player.id == player_id:
                self.state.players.remove(player)
                return
        raise ValueError(f"Player {player_id} not in game players")

    def remove_player(self, player):
        if player not in self.state.players:
            raise ValueError("Player {} not in game players".format(player))
        self.state.players.remove(player)

    def initialize(self):
        """
        Perform game environment initialization
        """
        for component in self.components:
            component.initialize()
        self.state.phase = GamePhase.READY_TO_START

    @property
    def id(self):
        return self._id

    @property
    def is_finished(self):
        return self.state.phase in [GamePhase.COMPLETED, GamePhase.ERROR]

    @property
    def is_running(self):
        return self.state.phase not in [GamePhase.INITIALIZATION, GamePhase.ERROR, GamePhase.COMPLETED]

    def start_game(self):
        """
        Step from INITIALIZE into first TURN_SETUP
        """
        self.log("Starting game")
        if not self.state.phase == GamePhase.INITIALIZATION:
            raise RuntimeError("Attempted to start game while in non-initialize")
        self.state.phase = GamePhase.TURN_SETUP

    def step_loop(self):
        """
        Step forward one phase in the main turn loop.

        TODO: handle with asyncio instead of threading?
        """
        if self.state.phase == GamePhase.TURN_SETUP:
            # run turn setup actions
            for component in self.components:
                component.turn_setup()
            self.state.phase = GamePhase.TURN_DECLARE_TEAM
            return
        if self.state.phase == GamePhase.TURN_DECLARE_TEAM:
            # this is just a UI phase, don't do anything
            if self.state.t_phase_elapsed == 0:
                self.state.t_phase_duration = 15.0
                self.state.t_phase_elapsed += 0.05
            elif self.state.t_phase_duration - self.state.t_phase_elapsed < 0:
                self.state.t_phase_elapsed = 0
                self.state.phase = GamePhase.TURN_PREPARE_TEAM
            else:
                self.state.t_phase_elapsed += 0.05
                time.sleep(0.05)
            return
        if self.state.phase == GamePhase.TURN_PREPARE_TEAM:
            # this is just a UI phase, don't do anything
            if self.state.t_phase_elapsed == 0:
                self.state.t_phase_duration = 15.0
                self.state.t_phase_elapsed += 0.05
            elif self.state.t_phase_duration - self.state.t_phase_elapsed < 0:
                self.state.t_phase_elapsed = 0
                self.state.phase = GamePhase.TURN_EXECUTE
            else:
                self.state.t_phase_elapsed += 0.05
                time.sleep(0.05)
            return
        if self.state.phase == GamePhase.TURN_EXECUTE:
            for component in self.components:
                component.turn_execute()
            self.state.phase = GamePhase.TURN_CLEANUP
            return
        if self.state.phase == GamePhase.TURN_CLEANUP:
            for component in self.components:
                component.turn_cleanup()
            self.state.phase = GamePhase.TURN_COMPLETE
            return
        if self.state.phase == GamePhase.TURN_COMPLETE:
            # this is just a UI phase, don't do anything
            if self.state.t_phase_elapsed == 0:
                self.state.t_phase_duration = 15.0
                self.state.t_phase_elapsed += 0.05
            elif self.state.t_phase_duration - self.state.t_phase_elapsed < 0:
                self.state.t_phase_elapsed = 0
                self.state.phase = GamePhase.TURN_SETUP
            else:
                self.state.t_phase_elapsed += 0.05
                time.sleep(0.05)
            return
        if self.state.phase == GamePhase.READY_TO_START:
            # ok move it on in
            self.state.phase = GamePhase.TURN_SETUP
            return

        raise RuntimeError(f"Game phase not in main turn loop yet. Phase {self.state.phase}")
