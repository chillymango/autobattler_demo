from enum import Enum


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
    READY_TO_START = 1
    TURN_SETUP = 2
    TURN_DECLARE_TEAM = 3
    TURN_PREPARE_TEAM = 4
    TURN_PREP = 5
    TURN_EXECUTE = 6
    TURN_CLEANUP = 7
    TURN_COMPLETE = 8
    CLEANUP = 9
    COMPLETED = 10
    ERROR = 11
