from enum import Enum


class CombatHook(Enum):
    """
    Combat Phases
    """

    INSTANT = 0
    PRE_BATTLE = 1
    PRE_COMBAT = 2
    ON_TICK = 3
    ON_FAST_MOVE = 4
    ON_ENEMY_FAST_MOVE = 5
    ON_CHARGED_MOVE = 6
    ON_ENEMY_CHARGED_MOVE = 7
    POST_COMBAT = 8
    POST_BATTLE = 9
    POST_MALONE = 10
