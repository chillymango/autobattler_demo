from engine.env import Environment
from engine.models.player import EntityType, Player
from engine.pokemon import PokemonFactory
from engine.batterulogico import *

class TestEnvironment(Environment):
    """
    Only load the things we care about testing.

    In this case just load the PokemonFactory
    """

    @property
    def component_classes(self):
        return [PokemonFactory]


env = TestEnvironment(8)
env.initialize()
#factory = PokemonFactory(env, env.state)
factory = env.pokemon_factory
a0 = factory.create_pokemon_by_name("charmander")
b0 = factory.create_pokemon_by_name("squirtle")
c0 = factory.create_pokemon_by_name("bulbasaur")
d0 = factory.create_pokemon_by_name("bulbasaur")
e0 = factory.create_pokemon_by_name("squirtle")
f0 = factory.create_pokemon_by_name("charmander")


poke_list = [a0, b0, c0, d0, e0, f0]
card_list = [x.battle_card for x in poke_list]

team1 = []
team2 = []

for index, x in enumerate(card_list):
    # x.a_iv = x.d_iv = 1
    # x.hp_iv = 50
    # x.health = 100
    if index < 3:
        team1.append(x)
    else:
        team2.append(x)


# print(battle(team1, team2))

masterlist = ['mewtwo', 'zapdos', 'articuno', 'moltres', 'blastoise', 
'exeggutor', 'gyarados', 'charizard', 'dragonite', 'lapras', 
'rhydon', 'venusaur', 'arcanine', 'vaporeon', 'ninetales_alolan', 
'chansey', 'kangaskhan', 'tauros', 'clefable', 'rapidash', 'wigglytuff', 
'pinsir', 'aerodactyl', 'vileplume', 'slowbro', 'machamp', 'alakazam', 
'golem', 'gengar', 'jolteon', 'flareon', 'tentacruel', 'magneton', 
'marowak_alolan', 'parasect', 'golbat', 'persian_alolan', 'hitmonlee', 
'sandslash_alolan', 'magmar', 'electabuzz', 'hitmonchan', 'tangela', 
'raichu', 'jynx', 'scyther', 'porygon', 'fearow', 'gloom', 'machoke', 
'haunter', 'graveler', 'kadabra', 'charmeleon', 'wartortle', 'tentacool', 
'ponyta', 'beedrill', 'ivysaur', 'rhyhorn', 'dragonair', 'butterfree', 
'slowpoke', 'growlithe', 'onix', 'raticate_alolan', 'clefairy', 
'exeggcute', 'oddish', 'vulpix_alolan', 'cubone', 'eevee', 'magnemite', 
'paras', 'bulbasaur', 'charmander', 'squirtle', 'diglett', 'pikachu', 
'sandshrew_alolan', 'jigglypuff', 'spearow', 'zubat', 'rattata_alolan', 
'metapod', 'meowth_alolan', 'kakuna', 'dratini', 'caterpie', 'weedle', 
'magikarp']
# mew and snorlax are bugged. superpower vs super_power?

graph = []
poke1 = None
poke2 = None
for x in masterlist:
    poke1 = factory.create_pokemon_by_name(x).battle_card
    row = []
    for y in masterlist:
        poke2 = factory.create_pokemon_by_name(y).battle_card
        # team1 = [poke1, poke1, poke1]
        # team2 = [poke2, poke2, poke2]
        result = battle([poke1], [poke2])
        row.append(result)
    
    graph.append(row)

# prints winner

# abc = ''
# for x in masterlist:
#     abc += x+', '
# print('       '+abc)
# print('______________________________')

# for i, x in enumerate(graph):
#     sideways = ''
#     for j, y in enumerate(x):
#         if y["winner"] == "team1":
#             sideways += masterlist[i]+', '
#         elif y["winner"] == "team2":
#             sideways += masterlist[j]+', '
#         elif y["winner"] == "tie":
#             sideways += 'tie   , '
#         else:
#             print(y["error"])
#     print(masterlist[i]+':: '+sideways+'\n')

# prints damage chart

# print('       '+abc)
# print('______________________________')
# for i, x in enumerate(graph):
#     sideways = ''
#     for j, y in enumerate(x):
#         sideways += str(math.floor((y["team1damagedealt"][0]-y["team2damagedealt"][0])))+',     '
#     print(masterlist[i]+':: '+sideways+'\n')

import csv
fields = ['']
for x in masterlist:
    fields.append(x)
allrows = []
for i, x in enumerate(graph):
    row = [masterlist[i]]
    for j, y in enumerate(x):
#        row.append(round(((y["team1damagedealt"][0]-y["team2damagedealt"][0]))/(y["team1damagedealt"][0]+1), 3)*100)
        row.append(round((y["team1damagedealt"][0]/((y["team1damagetaken"][0])+0.1)), 3)*100)
    allrows.append(row)
filename = "sample_results_with_tick.csv"
with open(filename, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
    csvwriter.writerows(allrows)
