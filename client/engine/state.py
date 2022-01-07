"""
Game state should be stored here or something
"""
import typing as T
from engine.battle import BattleManager
from engine.match import Matchmaker
from engine.player import EntityType
from engine.player import Player
from engine.player import PlayerManager
from engine.shop import ShopManager
from engine.turn import Turn


class GamePhase:
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
            Matchmaker,
            ShopManager,
            BattleManager,
        ]

    def __init__(self, players: T.List[Player]):
        self.phase = GamePhase.INITIALIZATION
        self.players = players
        self.components = []

        self.current_player = self.players[0]

        for component in self.component_classes:
            self.components.append(component(self))


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
