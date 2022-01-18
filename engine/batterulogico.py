# this is a reference for available features of a battlecard
#     self.name = name
#     self.move_f = move_f
#     self.move_ch = move_ch
#     self.move_tm = move_tm
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

import json
import copy

import os.path
current_directory = os.path.dirname(__file__)
parent_directory = os.path.split(current_directory)[0]
parent_directory = os.path.split(parent_directory)[0]
file_path = os.path.join(parent_directory,'battle_engine/src/data/gamemaster.json')
# with open('../../battle_engine/src/data/gamemaster.json', 'r') as origin:
with open(file_path, 'r') as origin:
    dataset = json.load(origin)
    pokedex = {x["speciesId"] : x for x in dataset["pokemon"]} # creates a list of all pokemon
    moves = {x["moveId"] : x for x in dataset["moves"]} # creates a list of all moves
    types = dataset['types'] # creates a list of all types and their attributes
    
# current_team1_hp = current_team1.hp_iv*pokedex[current_team1.name]["baseStats"]["hp"]
# current_team2_hp = current_team2.hp_iv*pokedex[current_team2.name]["baseStats"]["hp"]

# I assume pokemon health doesn't initialize to 0, but if it does, need to create base stats for the pokemon

def battle(team1_cards, team2_cards): # takes two arrays of battlecards
    team1_live = copy.deepcopy(team1_cards) # create an instance of the team for the battle
    team2_live = copy.deepcopy(team2_cards)
    current_team1 = team1_live[0] # picks the leading pokemon
    current_team2 = team2_live[0]

    # this breaks if there are not three pokemon
    bench1 = [team1_live[1], team1_live[2]] # creates the initial bench for the team
    bench2 = [team2_live[1], team2_live[2]]
    team1_switches = 5 # max number of switches the team can make
    team2_switches = 5
    
    while (len(team1_live) != 0 and len(team2_live) != 0): # while there are pokemon alive for a team
        can_attack_1 = True # if a team switches out a pokemon, they won't get an attack this turn
        can_attack_2 = True

        # if bad matchup, switch
        index1 = check_advantage(current_team1, current_team2, bench1) # the index on bench for best pokemon
        index2 = check_advantage(current_team2, current_team1, bench2)
        if index1 >= 0 and team1_switches > 0: # if the current pokemon is not best
            current_team1, bench1 = swap_pokemon(current_team1, bench1, index1)
            print('team 1 has swapped '+bench1[index1].name+' with '+current_team1.name)
            can_attack_1 = False # can no longer attack this round
            team1_switches -= 1
        if index2 >= 0 and team2_switches > 0:
            current_team2, bench2 = swap_pokemon(current_team2, bench2, index2)
            print('team 2 has swapped '+bench2[index2].name+' with '+current_team2.name)
            can_attack_2 = False
            team2_switches -= 1
       
        # was considering making array of possible moves, but handled in optimal moves function

        pokemon1_dead = False # at the resolution of a turn, will decide if pokemon is switched   
        pokemon2_dead = False

        if can_attack_1: # pokemon 1 attacks
            pokemon2_dead = launch_attack(current_team1, current_team2)
        if can_attack_2:
            pokemon1_dead = launch_attack(current_team2, current_team1)
       
        if pokemon1_dead:
            print(current_team1.name+" fainted")
        if pokemon2_dead:
            print(current_team2.name+" fainted")

        if pokemon2_dead:
            current_team2 = next_pokemon(bench2) # handles the death of current pokemon
            team2_live.pop(0) # doesn't matter which pokemon is popped. once all three are gone it's over
        if pokemon1_dead:
            current_team1 = next_pokemon(bench1)
            team1_live.pop(0)

    # closing messages
    survivor1 = len(team1_live) # how many pokemon left on the team
    survivor2 = len(team2_live)
    if survivor1 == survivor2 == 0: # if they're equal, then they're both 0
        print('it was a hard-fought battle but ended in a tie')
    elif survivor1 == 3:
        print('you swept the other team')
    elif survivor2 == 3:
        print('you got wrecked')

    if survivor1 > 0:
        print('your team had '+str(survivor1)+' pokemon standing')
    elif survivor2 > 0:
        print('there were still '+str(survivor2)+' enemy pokemon')

def launch_attack(attacker, defender): # this is the bulk of battle logic. returns if damage was fatal. otherwise, directly changes battlecard data
    fatal = False # if the attack will be fatal
    # I THINK THE ELEMENT IN THE ARRAY IN MEMORY WILL BE CHANGED???
    # new_energy = attacker.energy # how much energy will change
    # shield_used = 0 # if a shield was used
    # new_health = defender.health # defender's new health

    # if fast move lethal, use move because can't be shielded
    if is_lethal(attacker, attacker.move_f, defender, defender.health):
        print(attacker.name+' used '+attacker.move_f)
        fatal = True
    else:
        move = calculate_optimal_move(attacker, defender) # picks the move with the highest damage, in case a charged is type-disadvantaged
        if move == attacker.move_tm or move == attacker.move_ch: # if the optimal move needs energy
            print(attacker.name+' used '+move)
            attacker.energy -= moves[move]["energy"] # decrement energy
            damage = 0 # set to 0 because if you shield a charged attack its useless
            effectiveness = -1 # how effective an attack was

            # check for shield
            if defender.bonus_shield > 0:
                defender.bonus_shield -= 1 # if shield, decrement
                print(defender.name+' used a shield')
            else:
                damage, effectiveness = calculate_damage(attacker, move, defender) # if no shield, does damage
            defender.health -= damage # deal damage
            print(defender.name+' took '+str(damage)+' damage')
            if effectiveness > 1.6:
                print('it was super effective')
            elif effectiveness > 1.3:
                print('it was kind of effective')
            elif effectiveness < 0.4:
                print('it was barely effective')
            elif effectiveness < 0.6:
                print('it was not very effective')

            if defender.health <= 0: # check if dead
                fatal = True

        else: # if the optimal move was a fast move
            print(attacker.name+' used '+attacker.move_f)
            attacker.energy += moves[attacker.move_f]["energyGain"] # gain energy
            print(attacker.name+' is charging up')
            damage, effectiveness = calculate_damage(attacker, move, defender)
            defender.health -= damage
            print(defender.name+' took '+str(damage)+' damage')
            if defender.health <= 0: # check if dead
                fatal = True

    # max_health = pokedex[defender.name]["health"] # this line would be for flavor text of how the pokemon is doing
    if defender.health > 50: # I picked a random number. could do percent of max health but harder
        print(defender.name+' is looking healthy')
    elif defender.health > 20:
        print(defender.name+' isn\'t looking great')
    elif defender.health > 1:
        print(defender.name+' is close to fainting')
    elif defender.health > 0 and defender.health <= 1:
        print('call an ambulance!') # consider returning a flag, and if this pokemon almost died, add "but not for me"

    return fatal

def next_pokemon(bench): # takes in bench of team, returns new pokemon and modifies bench
    if len(bench) >0:
        return bench.pop(0)
    else:
        return None

def swap_pokemon(current, bench, index): # takes in pokemon, bench, and index of new pokemon. returns a pokemon and an array for the bench
    holder = bench[index]
    bench[index] = current
    return holder, bench

def check_advantage(attacker, defender, bench): # (attacker's bench). returns -1 if current is best. returns index on bench if better pokemon
    if analyze_type(attacker, defender) < 0: # can change this value if don't want to switch as often
        for i, x in enumerate(bench): # checks pokemon on the bench
            if analyze_type(x, defender) > 0:
                return i # return the index of the type-advantaged pokemon
    return -1 # no *significantly* better pokemon to switch to

def analyze_type(attacker, defender): # >0 is good, <0 is bad
    # these lines pull the types of the moves
    attacker_fast = moves[attacker.move_f]["type"]
    attacker_charged = moves[attacker.move_ch]["type"]
    attacker_tm = moves[attacker.move_tm]["type"]
    defender_fast = moves[defender.move_f]["type"]
    defender_charged = moves[defender.move_ch]["type"]
    defender_tm = moves[defender.move_tm]["type"]
    
    attacker_type = [] # initialize the array of move types
    defender_type = []

    attacker_self = pokedex[attacker.name]["types"] # the pokemon's types
    defender_self = pokedex[defender.name]["types"]

    # if-else that creates array of available attack types. to avoid dodging a tem attack when they don't have it available. can change this to simulate uncertainty of enemy team
    if attacker.tm_flag == 1: # if the tm is available
        attacker_type = [attacker_fast, attacker_charged, attacker_tm]
    else:
        attacker_type = [attacker_fast, attacker_charged] # ignoring if the charged attack is available, for now

    if defender.tm_flag == 1:
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
        attacker_resistances += types[x]["resistances"]
        attacker_weaknesses += types[x]["weaknesses"]
        attacker_immunities += types[x]["immunities"]
    for x in defender_self:
        defender_resistances += types[x]["resistances"]
        defender_weaknesses += types[x]["weaknesses"]
        defender_immunities += types[x]["immunities"]

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
    
def calculate_optimal_move(attacker, defender): # returns string, the name of best move
    # can consider passing back a flag for if the move was effective or not, to print. or change in calculate_damage
    fast_damage = calculate_damage(attacker, attacker.move_f, defender)[0]
    charged_damage = -1 # assume it's not available
    tm_damage = -1

    if attacker.energy >= moves[attacker.move_ch]['energy']: # if you can use charged attack
        charged_damage = calculate_damage(attacker, attacker.move_ch, defender)[0]

    if attacker.tm_flag == 1 and attacker.energy >= moves[attacker.move_tm]['energy']: # if you can use tm attack
        tm_damage = calculate_damage(attacker, attacker.move_tm, defender)[0]

    if fast_damage >= charged_damage and fast_damage >= tm_damage:
        return attacker.move_f
    elif charged_damage >= tm_damage:
    # could add logic about using the cheaper attack or whatever
        return attacker.move_ch
    return attacker.move_tm    

def calculate_damage(attacker, move, defender): # battlecard, string, battlecard. returns damage
    attacker_type = pokedex[attacker.name]["types"] # gives an array of strings that are the types
    attacker_attack = attacker.a_iv*pokedex[attacker.name]["baseStats"]["atk"] # defines which attack
    move_type = moves[move]["type"] # gets the type of the move from the dictionary "moves"
    power = moves[move]["power"] # base power of move

    defender_type = pokedex[defender.name]["types"] # gives an array of strings that are the types
    defender_defense = defender.d_iv*pokedex[defender.name]["baseStats"]["def"]
    
    defender_resistances = []
    defender_weaknesses = []
    defender_immunities = []
    # need to make resistances into it's own function. see "analyze_type"
    for x in defender_type:
        defender_resistances += types[x]["resistances"]
        defender_weaknesses += types[x]["weaknesses"]
        defender_immunities += types[x]["immunities"]
    
    multiplier = 1 # how much the damage is influenced
    if move_type in attacker_type:
        multiplier *= 1.5
    if move_type in defender_resistances:
        multiplier *= 0.625
    if move_type in defender_weaknesses:
        multiplier *= 1.6
    if move_type in defender_immunities:
        multiplier *= 0.4 # make this 0 if you're real

    return multiplier*power*attacker_attack/defender_defense, multiplier

def is_lethal(attacker, move, defender, defender_health): # checks if damage would be lethal
    if calculate_damage(attacker, move, defender)[0] >= defender_health:
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