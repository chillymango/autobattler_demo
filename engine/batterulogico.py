# this is a reference for available features of a battlecard
#     self.name.name = name
#     self.move_f.name = move_f.name
#     self.move_ch.name = move_ch.name
#     self.move_tm.name = move_tm.name
#     self.level = int(level)
#     self.a_iv = int(a_iv)
#     self.d_iv = int(d_iv)
#     self.hp_iv = int(hp_iv)
#     self.tm_flag = tm_flag
#     self.shiny = shiny
#     self.health = health
#     self.energy = energy
#     self.bonus_shield = bonus_shield
#     self.status = status  

# pre_battle_action()
# pre_combat_action()
# on_tick_action()
# on_fast_move_action()
# on_charged_move_action()
# post_combat_action
# post_battle_action

# import typing as T
# from engine.models.itmes import Item

# pre battle hooks
# step 1 determine what the relevant items are and who they belong to
# team1_items = set([x.berry for x in ...
# context
# context.update() at every item check
# for item in team1 items
# item.pre_battle_action(context)

# make a class BattleContext(BaseModel):
# name: str
# move_f.name: str
# atk: int
# : T.List[Battler]

# class Battler(BaseModel):
# atk: float = 0
# def __init__(self, battle_card, index, **kwargs):
# self

# @classmethod
# def create(cls, 
# return cls(atk=atk)

# import pydantic import BaseModel


import json
import copy
import math
import typing as T
from random import randint

import os.path
from engine.models.enums import Move, PokemonId
from engine.models.battle import BattleEvent, Event
from engine.models.combat_hooks import CombatHook
from engine.models.pokemon import SHINY_STAT_MULT, BattleCard
from engine.models.weather import WeatherType

if T.TYPE_CHECKING:
    from engine.models.items import CombatItem

current_directory = os.path.dirname(__file__)
parent_directory = os.path.split(current_directory)[0]
parent_directory = os.path.split(parent_directory)[0]
file_path = os.path.join(parent_directory,'autobattler_demo/battle_engine/src/data/gamemaster.json')
# with open('../../battle_engine/src/data/gamemaster.json', 'r') as origin:
with open(file_path, 'r') as origin:
    dataset = json.load(origin)
    #pokedex = {x["speciesId"] : x for x in dataset["pokemon"]} # creates a list of all pokemon

#    moves = {x["moveId"] : x for x in dataset["moves"]} # creates a list of all moves
# issue where SUPERPOWER is a move, but super_power is the id, basically
    moves = {x["moveId"] : x for x in dataset["moves"]} # not name

    types = dataset['types'] # creates a list of all types and their attributes
    # how combat power modifies
    # cpms = dataset["cpms"] or whatever
cpms = [0.0939999967813491, 0.135137430784308, 0.166397869586944, 0.192650914456886, 0.215732470154762, 0.236572655026622, 0.255720049142837, 0.273530381100769, 0.290249884128570, 0.306057381335773, 0.321087598800659, 0.335445032295077, 0.349212676286697, 0.362457748778790, 0.375235587358474, 0.387592411085168, 0.399567276239395, 0.411193549517250, 0.422500014305114, 0.432926413410414, 0.443107545375824, 0.453059953871985, 0.462798386812210, 0.472336077786704, 0.481684952974319, 0.490855810259008, 0.499858438968658, 0.508701756943992, 0.517393946647644, 0.525942508771329, 0.534354329109191, 0.542635762230353, 0.550792694091796, 0.558830599438087, 0.566754519939422, 0.574569148039264, 0.582278907299041, 0.589887911977272, 0.597400009632110, 0.604823657502073, 0.612157285213470, 0.619404110566050, 0.626567125320434, 0.633649181622743, 0.640652954578399, 0.647580963301656, 0.654435634613037, 0.661219263506722, 0.667934000492096, 0.674581899290818, 0.681164920330047, 0.687684905887771, 0.694143652915954, 0.700542893277978, 0.706884205341339, 0.713169102333341, 0.719399094581604, 0.725575616972598, 0.731700003147125, 0.734741011137376, 0.737769484519958, 0.740785574597326, 0.743789434432983, 0.746781208702482, 0.749761044979095, 0.752729105305821, 0.755685508251190, 0.758630366519684, 0.761563837528228, 0.764486065255226, 0.767397165298461, 0.770297273971590, 0.773186504840850, 0.776064945942412, 0.778932750225067, 0.781790064808426, 0.784636974334716, 0.787473583646825, 0.790300011634826, 0.792803950958807, 0.795300006866455, 0.797803921486970, 0.800300002098083, 0.802803892322847, 0.805299997329711, 0.807803863460723, 0.810299992561340, 0.812803834895026, 0.815299987792968, 0.817803806620319, 0.820299983024597, 0.822803778631297, 0.825299978256225, 0.827803750922782, 0.830299973487854, 0.832803753381377, 0.835300028324127, 0.837803755931569, 0.840300023555755, 0.842803729034748, 0.845300018787384, 0.847803702398935, 0.850300014019012, 0.852803676019539, 0.855300009250640, 0.857803649892077, 0.860300004482269, 0.862803624012168, 0.865299999713897]

# current_team1_hp = current_team1.hp_iv*pokedex[current_team1.name.name]["baseStats"]["hp"]
# current_team2_hp = current_team2.hp_iv*pokedex[current_team2.name.name]["baseStats"]["hp"]

# I assume pokemon health doesn't initialize to 0, but if it does, need to create base stats for the pokemon

class Battler:
    def __init__(self, battle_card: BattleCard, index: int, team: str):
        self.battlecard = battle_card # so it knows what kind of pokemon it is
        self.battlecard.bonus_shield = 1
        self.team = team

        # initialize stats. ignoring iv for now
        self.a = battle_card.attack
        self.d = battle_card.defense
        self.hp = self.battlecard.hitpoints
        if self.hp < 10:
            self.hp = 10

        self.id = index # keep track of where on the bench it is. for keeping track of how much damage it does
        self.dmg_dealt = 0
        self.dmg_taken = 0
        self.ready = False
        self.timer = 0

        # buff modifiers
        self.am = 0
        self.dm = 0

        # can look at pokemon.js line 595 "self.activechargedmoves = []" to see sorting charged move array by cost, selecting an optimal move

        # should maybe do energy and shields also, because currently I'm just using the battle_card info, which ideally isn't changed because the object isn't meant for that


class Effectiveness:

    def __init__(self):
        self.eff: float = 1.0

class render:
    def move_name_cleaner(move):
        move = move.replace(" ", "")
        move = move.replace("_", " ")
        return(move.title())
    
    def __call__(self):
        return

class EventLogger:
    """
    Keeps track of the global tick and all events that occur.

    Sorts them automatically.

    Eventually can use something similar to implement some sort of action queue.
    """

    def __init__(self):
        self.global_timer = 0
        self.sequence_idx = 0
        self.events: T.List[Event] = []

    def increment_timer(self, incr: float):
        """
        Increment the global timer by some amount.
        """
        self.global_timer += incr

    def __call__(self, category: str, msg: str):
        """
        Log a message. Append a message to the list of events.
        """
        self.events.append(
            BattleEvent(
                seq=self.sequence_idx,
                timestamp=self.global_timer,
                category=category,
                value=msg
            )
        )
        self.sequence_idx += 1


class HookExecutor:

    def __init__(
        self,
        team1: T.List[BattleCard],
        team2: T.List[BattleCard],
        logger: EventLogger = None,
    ):
        self.team1 = team1
        self.team2 = team2
        self.logger = logger

        self.team1_items = self.get_all_team_items(self.team1)
        self.team2_items = self.get_all_team_items(self.team2)

    def get_all_team_items(self, team: T.List[BattleCard]):
        """
        Get all items
        """
        return [poke.item for poke in team]

    def get_active_team_items(self, team: T.List[BattleCard], active: Battler, hook: "CombatHook"):
        """
        Get active team items for a combat hook
        """
        # determine the active items
        # for pre / post-battle hooks, all item effects should always trigger by default
        if hook in (CombatHook.PRE_BATTLE, CombatHook.POST_BATTLE):
            return self.get_all_team_items(team)

        # all global items are active (including *beyond the grave*)
        # remote items are active if the holding pokemon is not fainted
        # other items are only active if the pokemon is currently in combat
        team_items = [None] * 3
        for idx, teammate in enumerate(team):
            if active is not None and active.battlecard == teammate:
                team_items[idx] = teammate.item
            elif teammate.item:
                if teammate.item.is_global:
                    team_items[idx] = teammate.item
                elif teammate.item.is_remote and teammate.status:
                    team_items[idx] = teammate.item

        return team_items

    def __call__(
        self,
        hook: "CombatHook",
        current_team1: Battler,
        current_team2: Battler,
        **context: T.Dict
    ) -> None:
        """
        Run combat item execution
        """
        context = context or dict()

        # determine the active items
        # for pre / post-battle hooks, all item effects should always trigger by default
        team1_items_list = self.get_active_team_items(self.team1, current_team1, hook)
        team1_items = {self.team1[idx]: team1_items_list[idx] for idx in range(len(self.team1))}
        team2_items_list = self.get_active_team_items(self.team2, current_team2, hook)
        team2_items = {self.team2[idx]: team2_items_list[idx] for idx in range(len(self.team2))}

        # run item callbacks
        active_items: T.List[T.Optional[CombatItem]] = team1_items_list + team2_items_list
        for item in active_items:
            if item is None:
                continue
            method = item.get_method(hook)
            if current_team1:
                battlecard1 = current_team1.battlecard
            else:
                battlecard1 = None
            if current_team2:
                battlecard2 = current_team2.battlecard
            else:
                battlecard2 = None

            method(
                logger=self.logger,
                current_team1=battlecard1,
                current_team2=battlecard2,
                team1=self.team1,
                team2=self.team2,
                team1_items=team1_items,
                team2_items=team2_items,
                **context
            )

INCREMENT = 100

# TODO(albert): this global is gross
execute_hook = None


def battle(
    team1_cards: T.List[BattleCard],
    team2_cards: T.List[BattleCard],
    weather: WeatherType = None
):
    """
    Takes two arrays of battle cards and simulates combat between them.

    The original battle cards are shallow-copied and modified during the battle.
    """
    # start a new logger for each battle
    logger = EventLogger()
    # TODO(albert): should this be cards or live?
    global execute_hook
    execute_hook = HookExecutor(team1_cards, team2_cards, logger=logger)

    #team1_items = {poke.item: team1_cards[poke] for poke in team1_cards}
    #team2_items = {poke.item: team2_cards[poke] for poke in team2_cards}
    global_timer = 0
    #print(f'{team1_items=}')
    #print(f'{team2_items=}')

    # TODO(albert/tone): calculate weather advantage

    stop_this = False

    # creating a dictionary for output
    output = {
        "winner": "none",
        "team1damagedealt": [],
        "team1damagetaken": [],
        "team2damagedealt": [],
        "team2damagetaken": [],
        "events": []
    }
    t1_dmg_dealt = []
    t1_dmg_taken = []
    t2_dmg_dealt = []
    t2_dmg_taken = []
    sequence = []
    
    team1_live: T.List[BattleCard] = copy.copy(team1_cards) # create an instance of the team for the battle
    team2_live: T.List[BattleCard] = copy.copy(team2_cards)

    bench1 = []
    bench2 = []

    for index, x in enumerate(team1_live):
        bench1.append(Battler(x, index, 'team 1'))
        logger("join_party", f"{x} joined team 1")
    for index, x in enumerate(team2_live):
        bench2.append(Battler(x, index, 'team 2'))
        logger("join_party", f"{x} joined team 2")

    # because I pop off the benches, and that leads to index problem when putting pokemon back at the end
    bench1_permanent = bench1
    bench2_permanent = bench2

    try:
        current_team1: Battler = bench1[0]
    except IndexError:
        current_team1 = None
    try:
        current_team2: Battler = bench2[0]
    except IndexError:
        current_team2 = None

    # current_team1 = team1_live[0] # picks the leading pokemon
    # current_team2 = team2_live[0]

    # bench1 = []
    # bench2 = []
    # for i in range(len(team1_live)):
    #     if i > 0:
    #         bench1.append(team1_live[i])
    # for i in range(len(team2_live)):
    #     if i > 0:
    #         bench2.append(team2_live[i])
    # # this breaks if there are not three pokemon
    # # bench1 = [team1_live[1], team1_live[2]] # creates the initial bench for the team
    # # bench2 = [team2_live[1], team2_live[2]]
    
    team1_switches = 5 # max number of switches the team can make
    team2_switches = 5
    turnnumber = 0

    # COMBAT ITEM HOOK: pre_battle_action
    execute_hook(CombatHook.PRE_BATTLE, current_team1, current_team2)

    combat_rising_edge = False

    while (len(team1_live) > 0 and len(team2_live) > 0 and stop_this == False): # while there are pokemon alive for a team
        turnnumber += 1
        logger("Turn", str(turnnumber))

        if not combat_rising_edge:            
            # announce current team members
            logger("team1_active", f"{current_team1.battlecard.name} is fighting for team 1")
            ### render("|switch|p1a: " + current_team1.battlecard.nickname +  "|" + current_team1.battlecard.nickname + "|" + str(int(current_team1.battlecard.max_health)) + r"\/" + str(int(current_team1.battlecard.max_health))" )
            logger("team2_active", f"{current_team2.battlecard.name} is fighting for team2")
            ### render("|switch|p2a: " + current_team2.battlecard.nickname +  "|" + current_team2.battlecard.nickname + "|" + str(int(current_team2.battlecard.max_health)) + r"\/" + str(int(current_team2.battlecard.max_health))" )

            # COMBAT ITEM HOOK: pre_combat_action
            execute_hook(CombatHook.PRE_COMBAT, current_team1, current_team2)
            combat_rising_edge = True

        # COMBAT ITEM HOOK: on_tick
        execute_hook(CombatHook.ON_TICK, current_team1, current_team2)

        # increment time
        logger.increment_timer(INCREMENT)
        current_team1.timer += INCREMENT
        current_team2.timer += INCREMENT

        move1 = calculate_optimal_move(current_team1, current_team2)
        move2 = calculate_optimal_move(current_team2, current_team1)
        if not move1 and not move2:
            continue

        can_attack_1 = True # if a team switches out a pokemon, they won't get an attack this turn
        can_attack_2 = True
        # if bad matchup, switch
# THIS NEEDS WORK, IF WANT TO TRY 1V1
        index1 = check_advantage(current_team1, current_team2, bench1) # the index on bench for best pokemon
        index2 = check_advantage(current_team2, current_team1, bench2)
#        index1 = matchup(current_team1, current_team2, bench1)
#        index2 = matchup(current_team2, current_team1, bench2)

        if index1 >= 0 and team1_switches > 0: # if the current pokemon is not best
            current_team1, bench1 = swap_pokemon(current_team1, bench1, index1)
            # print('team 1 has swapped '+bench1[index1].name.name+' with '+current_team1.name.name)
            logger("Switch", "team1")
            #render("|switch|p1a: "+current_team1.battlecard.nickname+"|"+current_team1.battlecard.nickname+"|"+ str(int(current_team1.battlecard.health)) + r"\/" + str(int(current_team1.battlecard.max_health)))
            

            #sequence.append(Event(-1, "switch", "team 1"))
            can_attack_1 = False # can no longer attack this round
            team1_switches -= 1
        if index2 >= 0 and team2_switches > 0:
            current_team2, bench2 = swap_pokemon(current_team2, bench2, index2)
            # print('team 2 has swapped '+bench2[index2].name.name+' with '+current_team2.name.name)
            logger("Switch", "team2")
            #render("|switch|p1a: "+current_team2.battlecard.nickname+"|"+current_team2.battlecard.nickname+"|"+ str(int(current_team2.battlecard.health)) + r"\/" + str(int(current_team2.battlecard.max_health)))

            #sequence.append(Event(-1, "switch", "team 2"))
            can_attack_2 = False
            team2_switches -= 1

        # was considering making array of possible moves, but handled in optimal moves function

        pokemon1_dead = False # at the resolution of a turn, will decide if pokemon is switched   
        pokemon2_dead = False

        dummy1 = copy.copy(current_team1)
        dummy2 = copy.copy(current_team2)
        dumseq = [] # copy.copy(sequence)
        dumdead1 = False
        dumdead2 = False
        if can_attack_1 and can_attack_2 and dummy1.timer >= 500 and dummy2.timer >=500:
            runtheblock = False
            firstset = [dummy1.battlecard.move_f.name, dummy1.battlecard.move_ch.name, dummy1.battlecard.move_tm.name]
            secondset = [dummy2.battlecard.move_f.name, dummy2.battlecard.move_ch.name, dummy2.battlecard.move_tm.name]
            for x in firstset:
                # consider an if_legal() function to check cooldown and tm flag, energy. though just adding cooldown check made the code slower
                # COULD USE IF_LEGAL IN CHOOSE OPTIMAL MOVE FUNCTION, or just take the code out of there
# the problem here is is_lethal changes the values, because I initially coded it as just a check, but turned it into a move
# would need to change the is_lethal function, correct the part in the battle loop. get rid of these deep copies then                
                dummy1_2 = copy.copy(dummy1)
                dummy2_2 = copy.copy(dummy2)
                if is_lethal(dummy1_2, x, dummy2_2, dummy2_2.hp, dumseq):
                    runtheblock = True
            for x in secondset:
                dummy1_2 = copy.copy(dummy1)
                dummy2_2 = copy.copy(dummy2)
                if is_lethal(dummy2_2, x, dummy1_2, dummy1_2.hp, dumseq):
                    runtheblock = True
            if runtheblock:
                dumdead2, firstattack = launch_attack(dummy1, dummy2, dumseq, logger)
                dumdead1, secondattack = launch_attack(dummy2, dummy1, dumseq, logger)
                wascharged1 = False
                wascharged2 = False
                if dummy1.battlecard.move_ch.name == firstattack or dummy1.battlecard.move_tm.name == firstattack:
                    wascharged1 = True
                if dummy2.battlecard.move_ch.name == secondattack or dummy2.battlecard.move_tm.name == secondattack:
                    wascharged2 = True
                priority = -1
                if wascharged1 and wascharged2:
                    # stat1 = effective_stat(dummy1, "a") # if debuffs/buffs changing base stats were what impacted the tiebreaker
                    # stat2 = effective_stat(dummy2, "a")
                    # print(stat1, stat2)
                    if dummy1.a > dummy2.a:
                        priority = 1
                    elif dummy2.a > dummy1.a:
                        priority = 2
                    elif dummy1.a == dummy2.a:
                        priority = 0
                elif wascharged1 and not wascharged2:
                    priority = 1
                elif wascharged2 and not wascharged1:
                    priority = 2
                elif not wascharged1 and not wascharged2:
                    priority = 0
                else:
                    print('help')
                if priority == -1:
                    print('help')
                if dumdead1 and dumdead2:
                    if priority == 1:
                        can_attack_2 = False
                    elif priority == 2:
                        can_attack_1 = False
                elif dumdead2 and not dumdead1:
                    # priority = 1
                    if wascharged2 and not wascharged1:
                        priority = 0
                    if priority == 1:
                        can_attack_2 = False
                elif dumdead1 and not dumdead2:
                    # priority = 2 # with this, if A has priority on double charged attack, but B has lethal, then A doesn't get the first attack
                    if wascharged1 and not wascharged2:
                        priority = 0
                    if priority == 2:
                        can_attack_1 = False

        if can_attack_1: # pokemon 1 attacks
            pokemon2_dead = launch_attack(current_team1, current_team2, sequence, logger)[0]
        if can_attack_2:
            pokemon1_dead = launch_attack(current_team2, current_team1, sequence, logger)[0]

        combat_over = False
        if pokemon1_dead:
            combat_over = True
            current_team1.battlecard.status = 0
            logger(
                "Team1 Faint",
                f"team 2 {current_team2.battlecard.name.name} KOs team 1 {current_team1.battlecard.name.name}"
            )
            #render("|faint|p1a: " + current_team1.battlecard.nickname)
        if pokemon2_dead:
            combat_over = True
            current_team2.battlecard.status = 0
            logger(
                "Team2 Faint",
                f"team 1 {current_team1.battlecard.name.name} KOs team 2 {current_team2.battlecard.name.name}"
            )
            #render("|faint|p2a: " + current_team2.battlecard.nickname)

        if combat_over:
            combat_rising_edge = False
            execute_hook(CombatHook.POST_COMBAT, current_team1, current_team2)

        if pokemon2_dead and current_team2.battlecard.status == 0:
            current_team2 = next_pokemon(bench2) # handles the death of current pokemon
            if current_team2 == None:
                stop_this = True
            team2_live.pop(0) # doesn't matter which pokemon is popped. once all three are gone it's over
        if pokemon1_dead and current_team1.battlecard.status == 0:
            current_team1 = next_pokemon(bench1)
            if current_team1 == None:
                stop_this = True
            team1_live.pop(0)

    # COMBAT ITEM HOOK: post_battle_action
    execute_hook(CombatHook.POST_BATTLE, current_team1, current_team2)

    # closing messages
    survivor1 = len(team1_live) # how many pokemon left on the team
    survivor2 = len(team2_live)
    if survivor1 == survivor2 == 0: # if they're equal, then they're both 0
        # print('it was a hard-fought battle but ended in a tie')
        output["winner"] = "tie"
    # elif survivor1 == 3:
        # print('you swept the other team')
    # elif survivor2 == 3:
        # print('you got wrecked')

    if survivor1 > 0:
        # print('your team had '+str(survivor1)+' pokemon standing')
        output["winner"] = "team1"
    elif survivor2 > 0:
        # print('there were still '+str(survivor2)+' enemy pokemon')
        output["winner"] = "team2"

    # return current pokemon to bench
#    bench1[current_team1.id] = current_team1
#    bench2[current_team2.id] = current_team2

    for index, x in enumerate(bench1_permanent):
        # t1_dmg_dealt[index] = x.dmg_dealt
        # t1_dmg_taken[index] = x.dmg_taken
        t1_dmg_dealt.append(x.dmg_dealt)
        t1_dmg_taken.append(x.dmg_taken)
    for index, x in enumerate(bench2_permanent):
        # t2_dmg_dealt[index] = x.dmg_dealt
        # t2_dmg_taken[index] = x.dmg_taken
        t2_dmg_dealt.append(x.dmg_dealt)
        t2_dmg_taken.append(x.dmg_taken)

    output["team1damagedealt"] = t1_dmg_dealt
    output["team1damagetaken"] = t1_dmg_taken
    output["team2damagedealt"] = t2_dmg_dealt
    output["team2damagetaken"] = t2_dmg_taken

    for index, x in enumerate(sequence):
        x.id = index

    output['events'] = logger.events

    return output


def launch_attack(
    attacker: Battler,
    defender: Battler,
    sequence: T.List[BattleEvent],
    logger: EventLogger
): # this is the bulk of battle logic. returns if damage was fatal. otherwise, directly changes battlecard data
    # THIS WILL CHANGE THE SEQUENCE BECAUSE OF POINTERS

    fatal = False # if the attack will be fatal
    # I THINK THE ELEMENT IN THE ARRAY IN MEMORY WILL BE CHANGED???
    # new_energy = attacker.energy # how much energy will change
    # shield_used = 0 # if a shield was used
    # new_health = defender.health # defender's new health

    move = calculate_optimal_move(attacker, defender) # picks the move with the highest damage, in case a charged is type-disadvantaged
    
    # if fast move lethal, use move because can't be shielded
    if is_lethal(attacker, attacker.battlecard.move_f.name, defender, defender.hp, sequence):
        # print(attacker.name.name+' used '+attacker.move_f.name)
        fatal = True
        move = attacker.battlecard.move_f.name
    else:
        if move == attacker.battlecard.move_tm.name or move == attacker.battlecard.move_ch.name: # if the optimal move needs energy
            # ON CHARGED MOVE COMBAT HOOKS: should run before damage calculations

            # COMBAT ITEM HOOK: on_charged_move
            execute_hook(CombatHook.ON_CHARGED_MOVE, attacker, defender, move=move)
            # COMBAT ITEM HOOK: on_enemy_charged_move
            execute_hook(CombatHook.ON_ENEMY_CHARGED_MOVE, attacker, defender, move=move)
            # print(attacker.name.name+' used '+move)
            logger(
                "Attack",
                f"{attacker.team} {attacker.battlecard.name.name} used {move} "
                f"on {defender.team} {defender.battlecard.name.name}"
            )
            #render("|-prepare|p" + str(attacker.team) + "a: " + attacker.battlecard.nickname + "|Geomancy")
            #render("|move|p" + str(attacker.team) + "a: " + attacker.battlecard.nickname + "|" + render.move_name_cleaner(move) + "|p" + str(defender.team) + "a: " +defender.battlecard.nickname)




            #attacker.battlecard.energy -= moves[move]["energy"] # decrement energy
            if move == attacker.battlecard.move_tm.name:
                attacker.battlecard.energy -= attacker.battlecard._move_tm_energy
            elif move == attacker.battlecard.move_ch.name:
                attacker.battlecard.energy -= attacker.battlecard._move_ch_energy
            else:
                raise Exception('what fuckin happened')

            logger(
                "Energy Use",
                f"{attacker.team} {attacker.battlecard.name.name} "
                f"has {attacker.battlecard.energy:.0f} energy left"
            )

            # idk about this, to simulate charged attack taking a while based on how it
            # looks when pvpoke renders a quick fast attack after opponent charged          
            attacker.timer = -500 # -= moves[move]["cooldown"] + 500 # an extra -500 to timer
            damage = 1 # set to 1 because if you shield a charged attack its useless
            effectiveness = -1 # how effective an attack was
            proposed_damage, p_effectiveness = calculate_damage(attacker, move, defender)

            # check for shield
            block = False
            if defender.battlecard.bonus_shield > 0:
                isweakbuff = False
                block = True
                try:
                    if moves[move]["buffTarget"] == "opponent" and float(moves[move]["buffApplyChance"]) == 1:
                        isweakbuff = True
                    elif moves[move]["buffTarget"] == "self":
                        isweakbuff = True
                except:
                    pass
                if isweakbuff and not is_lethal(attacker, move, defender, defender.hp, sequence):
                    fastDPT = calculate_damage(attacker, attacker.battlecard.move_f.name, defender)[0] / (moves[attacker.battlecard.move_f.name]["cooldown"] / 500)
                    if proposed_damage < (defender.hp / 1.5) and (fastDPT) <= 1.5: # opposite of battle.js line 2251 ("if the defender can't afford")
                        block = False
                if block:
                    defender.battlecard.bonus_shield -= 1 # if shield, decrement
                    # print(defender.name.name+' used a shield')
                    logger("Shield", f"{defender.team} {defender.battlecard.name.name} used a shield")
                    #render("|-singleturn|p"+defender.team+"a: "+defender.battlecard.nickname +"|Protect")
            if not block:
                damage = proposed_damage
                effectiveness = p_effectiveness
            defender.hp -= damage # deal damage
            defender.dmg_taken += damage
            attacker.dmg_dealt += damage

            hasbuff = False
            buff = []
            buff_target = ''
            chance = 0
            try:
                buff = moves[move]["buffs"]
                buff_target = moves[move]["buffTarget"]
                chance = float(moves[move]["buffApplyChance"]) * 1000
                hasbuff = True
            except:
                pass
            if hasbuff:
                a_modifier = int(buff[0])
                d_modifier = int(buff[1])
                luck = randint(1, 1000)
                # NOT TAKING INTO ACCOUNT MAXBUFFSTAGES YET. do with global setting for buffdivisor
                if chance >= luck:
                    if buff_target == "opponent":
                        if a_modifier != 0:
                            if a_modifier <0:
                                logger(
                                    "Attack Debuff",
                                    f"{attacker.team} {attacker.battlecard.name.name} debuffed {defender.battlecard.name.name}"
                                    
                                )
                                #render("|-unboost|p"+defender.team+"a: "+defender.battlecard.nickname+"|atk|"+str(a_modifier))
                            else:
                                logger(
                                    "Attack Buff",
                                    f"{attacker.team} {attacker.battlecard.name.name} buffed {defender.battlecard.name.name}"
                                )
                                #render("|-boost|p"+defender.team+"a: "+defender.battlecard.nickname+"|atk|"+str(a_modifier))
                                
                            defender.am += a_modifier
                        if d_modifier != 0:
                            if d_modifier < 0:
                                logger(
                                    "Defense Debuff",
                                    f"{attacker.team} {attacker.battlecard.name.name} debuffed {defender.battlecard.name.name}"
                                )
                                #render("|-unboost|p"+defender.team+"a: "+defender.battlecard.nickname+"|def|"+str(d_modifier))

                            else:
                                logger(
                                    "Defense Buff",
                                    f"{attacker.team} {attacker.battlecard.name.name} buffed {defender.battlecard.name.name}"
                                )
                                #render("|-boost|p"+defender.team+"a: "+defender.battlecard.nickname+"|def|"+str(d_modifier))

                            defender.dm += d_modifier
                    elif buff_target == "self":
                        if a_modifier != 0:
                            if a_modifier > 0:
                                logger(
                                    "Attack Buff",
                                    f"{attacker.team} {attacker.battlecard.name.name} buffed its own attack"
                                )
                                #render("|-boost|p"+attacker.team+"a: "+attacker.battlecard.nickname+"|atk|"+str(a_modifier))

                            else:
                                logger(
                                    "Attack Debuff",
                                    f"{attacker.team} {attacker.battlecard.name.name} debuffed its own attack"
                                )
                                #render("|-unboost|p"+attacker.team+"a: "+attacker.battlecard.nickname+"|atk|"+str(a_modifier))

                            attacker.am += a_modifier
                        if d_modifier != 0:
                            if d_modifier >0:
                                logger(
                                    "Defense Buff",
                                    f"{defender.team} {defender.battlecard.name.name} buffed its own defense"
                                )
                                #render("|-boost|p"+defender.team+"a: "+defender.battlecard.nickname+"|def|"+str(d_modifier))

                            else:
                                logger(
                                    "Defense Debuff",
                                    f"{defender.team} {defender.battlecard.name.name} debuffed its own defense"
                                )
                                #render("|-unboost|p"+defender.team+"a: "+defender.battlecard.nickname+"|def|"+str(d_modifier))

                            attacker.dm += d_modifier
            
            # print(defender.name.name+' took '+str(damage)+' damage')
            # if effectiveness > 1.6:
            #     print('it was super effective')
            # elif effectiveness > 1.3:
            #     print('it was kind of effective')
            # elif effectiveness < 0.4:
            #     print('it was barely effective')
            # elif effectiveness < 0.6:
            #     print('it was not very effective')

            # TRY TO TURN THIS INTO A DIFFERENT FUNCTION? definitely, given that it's used in lethal function
            how_was_it = ""
            if effectiveness > 1.6:
                how_was_it = 'it was super effective'
            elif effectiveness > 1.3:
                how_was_it = 'it was kind of effective'
            elif effectiveness < 0.4:
                how_was_it = 'it was barely effective'
            elif effectiveness < 0.6:
                how_was_it = 'it was not very effective'
            logger(
                "Charged Move Damage",
                f"{defender.team} {defender.battlecard.name.name} took {damage:.0f} damage: {how_was_it}"
            )
            #render("|-supereffective|p" + defender.team + "a: " + defender.battlecard.nickname) if effectiveness > 1
            #render("|-resisted|p" + defender.team + "a: " + defender.battlecard.nickname) if effectiveness < 1
            logger(
                "Health",
                f"{defender.team} {defender.battlecard.name.name} has {defender.hp:.0f} hp left"
            )
            #render("|-damage|p"+defender.team+"a: "+defender.battlecard.nickname + "|" + str(int(defender.hp)) + r"\/" + str(int(defender.battlecard.max_hp))")


            if defender.hp <= 0: # check if dead
                fatal = True

        elif move == attacker.battlecard.move_f.name: # if the optimal move was a fast move
            # COMBAT ITEM HOOK: on_fast_move_action
            # COMBAT ITEM HOOK: on_enemy_fast_move_action
            execute_hook(CombatHook.ON_FAST_MOVE, attacker, defender, move=move)
            execute_hook(CombatHook.ON_ENEMY_FAST_MOVE, attacker, defender, move=move)
            # print(attacker.name.name+' used '+attacker.move_f.name)
            logger(
                "Fast Attack",
                f"{attacker.team} {attacker.battlecard.name.name} used {attacker.battlecard.move_f.name} "
                f"on {defender.team} {defender.battlecard.name.name}"
            )
            #render("|move|p" + str(attacker.team) + "a: " + attacker.battlecard.nickname + "|" + render.move_name_cleaner(move) + "|p" + str(defender.team) + "a: " +defender.battlecard.nickname)

            #sequence.append(Event(-1, "attack", attacker.battlecard.name.name+" used "+attacker.battlecard.move_f.name+" on "+defender.battlecard.name.name))
            attacker.battlecard.energy += attacker.battlecard._move_f_energy
            logger(
                "Attack Charge Up",
                f"{attacker.team} {attacker.battlecard.name.name} now "
                f"has {attacker.battlecard.energy:.0f} energy"
            )
            #sequence.append(Event(-1, '', attacker.battlecard.name.name+" needs "+str(moves[attacker.battlecard.move_ch.name]["energy"] - attacker.battlecard.energy)+" more energy to use a charged move"))
            damage, effectiveness = calculate_damage(attacker, move, defender)
            defender.hp -= damage
            attacker.dmg_dealt += damage
            defender.dmg_taken += damage
            attacker.timer -= attacker.battlecard.atk_spd_timer_cts

            # print(defender.name.name+' took '+str(damage)+' damage')
            how_was_it = ""
            if effectiveness > 1.6:
                how_was_it = 'it was super effective'
            elif effectiveness > 1.3:
                how_was_it = 'it was kind of effective'
            elif effectiveness < 0.4:
                how_was_it = 'it was barely effective'
            elif effectiveness < 0.6:
                how_was_it = 'it was not very effective'
            #render("|-supereffective|p" + defender.team + "a: " + defender.battlecard.nickname) if effectiveness > 1
            #render("|-resisted|p" + defender.team + "a: " + defender.battlecard.nickname) if effectiveness < 1

            logger(
                "Fast Attack Damage",
                f"{defender.team} {defender.battlecard.name.name} took {damage:.0f} damage: {how_was_it}"
            )
            #render("|-damage|p"+defender.team+"a: "+defender.battlecard.nickname + "|" + str(int(defender.hp)) + r"\/" + str(int(defender.battlecard.max_hp))")
            
            logger(
                "Health",
                f"{defender.team} {defender.battlecard.name.name} has {defender.hp:.0f} HP left"
            )
            if defender.hp <= 0: # check if dead
                fatal = True
        else:
            pass

    # flavor text
    '''
    # max_health = pokedex[defender.name.name]["health"] # this line would be for flavor text of how the pokemon is doing
    if defender.health > 50: # I picked a random number. could do percent of max health but harder
        print(defender.name.name+' is looking healthy')
    elif defender.health > 20:
        print(defender.name.name+' isn\'t looking great')
    elif defender.health > 1:
        print(defender.name.name+' is close to fainting')
    elif defender.health > 0 and defender.health <= 1:
        print('call an ambulance!') # consider returning a flag, and if this pokemon almost died, add "but not for me"
    '''

    return fatal, move

def next_pokemon(bench): # takes in bench of team, returns new pokemon and modifies bench
    for x in bench:
        if x.hp > 0:
            return x
    return None
    # if len(bench) >0:
    #     return bench.pop(0)
    # else:
    #     return None

def swap_pokemon(current, bench, index): # takes in pokemon, bench, and index of new pokemon. returns a pokemon and an array for the bench
    # holder = bench[index]
    # bench[index] = current
    # return holder, bench
    holder = bench[index]
    bench[current.id] = current
    return holder, bench

# can just simulate a 1v1 to determine how the matchup is
def check_advantage(attacker, defender, bench): # (attacker's bench). returns -1 if current is best. returns index on bench if better pokemon
    if analyze_type(attacker, defender) < 0: # can change this value if don't want to switch as often
        for i, x in enumerate(bench): # checks pokemon on the bench
            if analyze_type(x, defender) > 0:
                return i # return the index of the type-advantaged pokemon
    return -1 # no *significantly* better pokemon to switch to

def matchup(attacker, defender, bench):
    if simulate1v1(attacker, defender) == "team 2":
        for i, x in enumerate(bench):
            if simulate1v1(x, defender) == "team 1":
                return i
    return -1

# this is too recursive. try the thing albert mentioned about memoization
def simulate1v1(attacker, defender):
    return battle([attacker.battlecard], [defender.battlecard])["winner"]

def analyze_type(attacker: Battler, defender: Battler, disabled=True): # >0 is good, <0 is bad
    # these lines pull the types of the moves
    attacker_fast = attacker.battlecard.f_move_type
    attacker_charged = attacker.battlecard.ch_move_type
    attacker_tm = attacker.battlecard.tm_move_type
    defender_fast = defender.battlecard.f_move_type
    defender_charged = defender.battlecard.ch_move_type
    defender_tm = defender.battlecard.tm_move_type
    
    attacker_type = [] # initialize the array of move types
    defender_type = []

    attacker_self = set([attacker.battlecard.poke_type1, attacker.battlecard.poke_type2])
    defender_self = set([defender.battlecard.poke_type1, defender.battlecard.poke_type2])

    # if-else that creates array of available attack types. to avoid dodging a tem attack when they don't have it available. can change this to simulate uncertainty of enemy team
    if attacker.battlecard.tm_flag == 1: # if the tm is available
        attacker_type = [attacker_fast, attacker_charged, attacker_tm]
    else:
        attacker_type = [attacker_fast, attacker_charged] # ignoring if the charged attack is available, for now

    if defender.battlecard.tm_flag == 1:
        defender_type = [defender_fast, defender_charged, defender_tm]
    else:
        defender_type = [defender_fast, defender_charged]

    attacker_resistances = []
    attacker_weaknesses = []
    attacker_immunities = []
    defender_resistances = []
    defender_weaknesses = []
    defender_immunities = []

    # this doesn't account for duplicate resistances/weaknesses
    # this pulls resistances
    for x in attacker_self:
        attacker_resistances += types[x.name]["resistances"]
        attacker_weaknesses += types[x.name]["weaknesses"]
        attacker_immunities += types[x.name]["immunities"]
    for x in defender_self:
        defender_resistances += types[x.name]["resistances"]
        defender_weaknesses += types[x.name]["weaknesses"]
        defender_immunities += types[x.name]["immunities"]

    # could make the multiplier stuff in calculate_damage its own function, instead of these discrete integers
    
    balance = 0 # start with neutral advantage
    for x in attacker_type:
        if x in defender_weaknesses:
            balance += 1
        if x in defender_resistances:
            balance -= 1
        if x in defender_immunities:
            balance -= 2
    for x in defender_type:
        if x in attacker_weaknesses:
            balance -= 1
        if x in attacker_resistances:
            balance += 1
        if x in attacker_immunities:
            balance += 2
    return balance


def calculate_optimal_move(attacker: Battler, defender: Battler): # returns string, the name of best move
    # can consider passing back a flag for if the move was effective or not, to print. or change in calculate_damage
    fast_damage = calculate_damage(attacker, attacker.battlecard.move_f.name, defender)[0]
    charged_damage = -1 # assume it's not available
    tm_damage = -1

    if attacker.battlecard.energy >= moves[attacker.battlecard.move_ch.name]['energy'] and attacker.timer >= moves[attacker.battlecard.move_ch.name]["cooldown"]: # if you can use charged attack
        charged_damage = calculate_damage(attacker, attacker.battlecard.move_ch.name, defender)[0]
    
    if attacker.battlecard.tm_flag == 1 and attacker.battlecard.energy >= moves[attacker.battlecard.move_tm.name]['energy'] and attacker.timer >= moves[attacker.battlecard.move_tm.name]["cooldown"]: # if you can use tm attack
        tm_damage = calculate_damage(attacker, attacker.battlecard.move_tm.name, defender)[0]
    
    holder = [charged_damage, tm_damage]
    holder2 = [attacker.battlecard.move_ch.name, attacker.battlecard.move_tm.name]
    for i, x in enumerate(holder2):
        if x in (None, 'none'):
            continue
        if moves[x]["archetype"] =="Self-Debuff":
            dontuse = False
            maxtimes = math.floor(attacker.battlecard.energy / moves[x]["energy"]) - defender.battlecard.bonus_shield
            theoreticaldamage = maxtimes * calculate_damage(attacker, x, defender)[0]
            turnsleft = turnstodie(attacker, defender)
            if theoreticaldamage > defender.hp and maxtimes < turnsleft:
                # attacker.timer += 500 * maxtimes # if the double charged attacks need to remove delay
                pass
            else:
                dontuse = True
# this is pvpoke "minimize time debuffed and it can stack the move" in battle.js                
            # if (defender.hp > holder[i] or defender.battlecard.bonus_shield > 0) and (attacker.hp > calculate_damage(defender, defender.battlecard.move_f.name, attacker) or moves[defender.battlecard.move_f.name]["cooldown" - moves[attacker.battlecard.move_f.name]["cooldown"] > 500]):
            #     dontuse = True


            if dontuse:
                holder[i] = -1
    charged_damage = holder[0]
    tm_damage = holder[1]

    if fast_damage >= charged_damage and fast_damage >= tm_damage and attacker.timer >= moves[attacker.battlecard.move_f.name]["cooldown"]:
        return attacker.battlecard.move_f.name
    elif charged_damage >= tm_damage and charged_damage > 0:
    # could add logic about using the cheaper attack or whatever
        return attacker.battlecard.move_ch.name
    elif tm_damage > 0:
        return attacker.battlecard.move_tm.name
    elif attacker.timer >= attacker.battlecard.atk_spd_timer_cts:
        return attacker.battlecard.move_f.name
    return ''


def turnstodie(me: Battler, them: Battler):
    myhp = me.hp
    theirenergy = them.battlecard.energy
    theirmovef = them.battlecard.move_f.name
    theirdps = calculate_damage(them, theirmovef, me)[0] * moves[theirmovef]["cooldown"] / 500
    whichcharged = ''
    if calculate_damage(them, them.battlecard.move_ch.name, me)[0] > calculate_damage(them, them.battlecard.move_tm.name, me)[0]:
        whichcharged = them.battlecard.move_ch.name
    else:
        whichcharged = them.battlecard.move_tm.name
    howmanytheircharged = 0
    while theirenergy > moves[whichcharged]["energy"]:
        howmanytheircharged += 1
        theirenergy -= moves[whichcharged]["energy"]
    myshields = me.battlecard.bonus_shield
    maxblocked = 0
    while myshields > 0:
        maxblocked += 1
        myshields -= 1
    chargedincoming = max(0, howmanytheircharged - myshields)
    turnstodie = 0
    while myhp > 0 and chargedincoming > 0:
        myhp -= calculate_damage(them, whichcharged, me)[0]
        chargedincoming -= 1
        turnstodie += 1
    while myhp > 0:
        myhp -= theirdps
        turnstodie += 1
    return turnstodie


def calculate_damage(attacker: Battler, move: Move, defender: Battler): # battlecard, string, battlecard. returns damage
    # this is theoretical damage

    #attacker_type = pokedex[attacker.battlecard.name.name]["types"] # gives an array of strings that are the types
    attacker_type = set((attacker.battlecard.poke_type1, attacker.battlecard.poke_type2))  # use set to dedupe
    # attacker_attack = attacker.a_iv*pokedex[attacker.name.name]["baseStats"]["atk"] # defines which attack
    #attacker_attack = attacker.a
    if move == attacker.battlecard.move_f.name:
        move_type = attacker.battlecard.f_move_type
        power = attacker.battlecard._move_f_damage
    elif move == attacker.battlecard.move_ch.name:
        move_type = attacker.battlecard.ch_move_type
        power = attacker.battlecard._move_ch_damage
    elif move == attacker.battlecard.move_tm.name:
        move_type = attacker.battlecard.tm_move_type
        power = attacker.battlecard._move_tm_damage

    #defender_type = pokedex[defender.battlecard.name.name]["types"] # gives an array of strings that are the types
    # defender_defense = defender.d_iv*pokedex[defender.name.name]["baseStats"]["def"]
    #defender_defense = defender.d
    defender_type = set((defender.battlecard.poke_type1, defender.battlecard.poke_type2))
    defender_resistances = []
    defender_weaknesses = []
    defender_immunities = []
    # need to make resistances into it's own function. see "analyze_type"
    for x in defender_type:
        defender_resistances += types[x.name]["resistances"]
        defender_weaknesses += types[x.name]["weaknesses"]
        defender_immunities += types[x.name]["immunities"]
    
    #multiplier = 1 # how much the damage is influenced
    multiplier = 1
    for x in attacker_type:
        if move_type == x:
            multiplier *= 1.2
    for x in defender_resistances:
        if move_type == x:
            multiplier *= 0.625
    for x in defender_weaknesses:
        if move_type == x:
            multiplier *= 1.6
    for x in defender_immunities:
        if move_type == x:
            multiplier *= 0.390625  # make this 0 if you're real

    atkstat = effective_stat(attacker, "a")
    defstat = effective_stat(defender, "d")
    # currently cannot implement buffs that help the opponent. maybe use function geteffectivestat() that pvpoke uses
    
    #return multiplier*power*attacker_attack/defender_defense, multiplier
    damage = math.floor(power * (atkstat/defstat) * multiplier  * 0.5 * 1.3) + 1 # 1.3 is bonusMultiplier. chargeMultiplier is how many circles you tap in minigame
    return damage, multiplier


def effective_stat(poke: Battler, which: str):
    # gamemaster.json has ""buffdivisor": 4"
    buffdivisor = 4
    if which == "a":
        if poke.am > 0:
            return poke.a * (buffdivisor + poke.am) / buffdivisor
        elif poke.am < 0:
            return poke.a * buffdivisor / (buffdivisor - poke.am)
        elif poke.am == 0:
            return poke.a
    elif which == "d":
        if poke.dm > 0:
            return poke.d * (buffdivisor + poke.dm ) / buffdivisor
        elif poke.dm < 0:
            return poke.d * buffdivisor / (buffdivisor - poke.dm)
        elif poke.dm ==0:
            return poke.d
    else:
        print("help")


def is_lethal(
    attacker: Battler,
    move: Move,
    defender: Battler,
    defender_hp: float,
    sequence: T.List[Event]
): # checks if damage would be lethal
    (damage, effectiveness) = calculate_damage(attacker, move, defender)
    if damage >= defender_hp and attacker.timer >= attacker.battlecard.atk_spd_timer_cts:
        sequence.append(Event(-1, "attack", attacker.battlecard.name.name+" used "+move+" on "+defender.battlecard.name.name))
        attacker.dmg_dealt += damage
        defender.hp -= damage
        defender.dmg_taken += damage
        attacker.timer = 0
        
        # this needs to be its own function
        how_was_it = ""
        if effectiveness > 1.6:
            how_was_it = 'it was super effective'
        elif effectiveness > 1.3:
            how_was_it = 'it was kind of effective'
        elif effectiveness < 0.4:
            how_was_it = 'it was barely effective'
        elif effectiveness < 0.6:
            how_was_it = 'it was not very effective'
        sequence.append(Event(-1, "damage", defender.battlecard.name.name+" took "+str(damage)+" damage. "+how_was_it))
        sequence.append(Event(-1, '', defender.battlecard.name.name+" now has "+str(defender.hp)+" hp left"))
        return True
    else:
        return False

# import mock

# from engine.player import EntityType, Player
# from engine.pokemon import PokemonFactory

# state = mock.MagicMock()
# state.players = [Player('a a', type_=EntityType.HUMAN)]

# pokemon_factory = PokemonFactory(state)
# x = pokemon_factory.create_pokemon_by_name("pikachu")
# print(x.health)
# from engine.batterulogico import *