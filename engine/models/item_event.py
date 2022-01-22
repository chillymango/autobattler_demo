import random
import typing as T
from pydantic import BaseModel
from pydantic import PrivateAttr

from engine.models.items import Item
from engine.models.player import Player

if T.TYPE_CHECKING:
    from engine.items import ItemManager

# what defines an item event?
# random item events could be:
#  guaranteed item
#  set of items with a different distribution


class ItemEvent(BaseModel):
    """
    Defines an event where a player gets an item randomly, or is given a choice of items.

    For example, on turn 7, a player is offered this choice of items.
    """

    turn: int  # turn that the item event occurs on
    player: Player  # player the item event happens for
    offered_items: T.List[str] = None  # a list of strings that correspond to item options


class GivenItemEvent(ItemEvent):
    """
    This is an event where a player is given a random item
    """


class ChosenItemEvent(ItemEvent):
    """
    This is an event where the player chooses an item
    """


# TODO: consolidate with shop into random utils
class Interval:
    """
    Util class that stores interval data and supports basic operations
    """

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def in_range(self, val, strict=False):
        if strict:
            return val > self.lower and val < self.upper
        return val >= self.lower and val <= self.upper


class TurnConfig(BaseModel):
    """
    Fully describes the item distribution by turn
    """

    item_set: T.Set[str]
    distribution: T.Dict[str, int]
    score: int = 0


class ItemSchedule(BaseModel):
    """
    Defines a schedule of distribution for item events

    For each turn, have a list of possible items, and the number of items to sample
    from the set of possible items.
    """

    turn_configs: T.Dict[int, TurnConfig]
    item_costs: T.Dict[str, int]
    all_known_items: T.Set[str]

    @classmethod
    def create_by_associations(
        cls,
        item_sets_by_turn: T.Dict[int, T.Set[str]],
        distribution_score_by_item: T.Dict[str, int],
        score_by_turn: T.Dict[int, int],
    ):
        all_known_items = set(list(item_sets_by_turn.keys()) + list(score_by_turn.keys()))
        turn_configs: T.Dict[int, TurnConfig] = {
            turn: TurnConfig(
                item_set=item_sets_by_turn.get(turn),
                score=score_by_turn.get(turn),
                distribution=distribution_score_by_item
            ) for turn in all_known_items
        }
        sched = cls(turn_configs=turn_configs, all_known_items=all_known_items)
        return sched

    def _valid_items_for_score(self, item_set: T.Set[str], score: int) -> T.Set[str]:
        """
        Given a score threshold (e.g items cannot exceed this score), return a set of valid items.
        """
        valid = set()
        for item in item_set:
            cost = self.item_costs[item]
            if cost <= score:
                valid.add(item)
        return valid

    def _sample_with_distribution(self, item_set: T.Set[str], dist: T.Dict[str, int]) -> str:
        """
        Given an item set and a distribution, sample a single item.

        Items need to be in both dist and item_set to be included.
        """
        dist_items = set(dist)
        if not item_set.intersection(dist_items):
            raise Exception("Item set and distribution do not overlap")

        # construct ranges
        intervals: T.List[T.Tuple[str, Interval]] = []
        counter = 0
        for item_name, score in dist.items():
            upper = counter + score
            intervals.append((item_name, Interval(counter, upper)))
            counter = upper

        # grab a number and check what range it's in
        rand = random.random() * upper
        for item_name, ival in intervals:
            if ival.in_range(rand):
                return item_name

    def roll_items(self, turn: int, score: int = None):
        """
        Acquire the turn config for a specific turn.

        If score is provided, use that in place of the default initialized.
        If score is not provided, use the default value provided in score_by_turn.

        While the score threshold has not been met, sample items one by one. When the score
        dips below the max item cost in the current item set, re-evaluate the allowed items.
        Continue until the score is met.
        """
        if turn not in self.turn_configs:
            # no item events this turn
            return

        # initialize the current set of items we can draw
        current_turn_config = self.turn_configs[turn]
        if not score and not current_turn_config.score:
            raise Exception("Invalid turn configuration. No item score provided.")
        elif not score:
            score = current_turn_config.score

        distributed_score = 0
        rolled_items: T.List[str] = []
        item_set = current_turn_config.item_set.copy()
        while distributed_score < score:
            item_set = self._valid_items_for_score(item_set, score - distributed_score)
            item_name = self._sample_with_distribution(item_set, current_turn_config.distribution)
            cost = self.item_costs[item_name]
            distributed_score += cost
            rolled_items.append(item_name)

        return rolled_items
