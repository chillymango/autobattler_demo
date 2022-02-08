"""
Helpers for building item schedules

NOTE: this shouldn't get imported. The outputs of this should be dumped into a JSON
that can be parsed by the item event manager at initialization.
"""
import random
import typing as T
from engine.models import items

from engine.models.item_event import ItemSchedule
from engine.models.item_event import TurnConfig
from engine.env import Environment
from engine.items import ItemManager
from engine.pokemon import PokemonFactory
from engine.match import CreepRoundManager, Matchmaker
from engine.turn import Turn


def build_basic_item_schedule(blocklisted_items: T.List[str] = None):
    """
    Item schedule generation rules:
    * at the beginning of each stage, give 10 +/- 2 in value
    * at the beginning of each creep round, give 3 +/- 1 in value
    """
    # create subenvironment for item and turn determination
    env = Environment(
        1,
        component_classes=[
            Turn,
            ItemManager,
            PokemonFactory,
            Matchmaker,
            CreepRoundManager
        ]
    )
    env.initialize()
    # all items available all the time...
    item_manager: ItemManager = env.item_manager
    all_items = set()
    item_types = (
        items.MasterBall,
        items.PokeFlute,
        items.Shard,
        items.CommonStone,
        items.TechnicalMachine,
        items.RareCandy
    )
    for itype in item_types:
        children = itype.__subclasses__()
        if children:
            for child in itype.__subclasses__():
                all_items.add(child.__name__)
        else:
            all_items.add(itype.__name__)

    if blocklisted_items:
        for blocklisted in blocklisted_items:
            all_items.discard(blocklisted)

    # distribution is always even (for now)
    distribution = {item_name: 1 for item_name in all_items}

    # come up with a random score to give every round
    # creep rounds are between 1 and 3
    # first round of a stage is between 5 and 10
    # there is no double-up of events (e.g creep rounds that are first rounds will apply first)
    turn: Turn = env.turn
    crm: CreepRoundManager = env.creep_round_manager
    # figure out stage transitions and creep rounds
    prev_stage = None
    turn_configs: T.Dict[int, TurnConfig] = dict()
    for turn_number, stage_config in turn.stages.items():
        if stage_config.stage != prev_stage:
            prev_stage = stage_config.stage
            score = random.randrange(25, 31)  # 11 to include 10, funny...
            turn_configs[turn_number] = TurnConfig(
                item_set=all_items,
                distribution=distribution,
                score=score,
            )
            continue

        # if same stage, check if creep round and give items if applicable
        creep_round = crm.creep_round_pokemon[turn_number]
        if creep_round:
            score = random.randrange(1, 4)
            turn_configs[turn_number] = TurnConfig(
                item_set=all_items,
                distribution=distribution,
                score=score
            )

    return ItemSchedule(
        turn_configs=turn_configs,
        all_known_items=all_items,
        item_costs=item_manager.item_costs,
    )


if __name__ == "__main__":
    sched = build_basic_item_schedule()
    import IPython; IPython.embed()
    with open('data/default_item_schedule.json', 'w+') as default_sched_file:
        default_sched_file.write(sched.json())
