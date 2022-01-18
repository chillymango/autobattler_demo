from engine.env import Environment
from engine.models.player import EntityType, Player
from engine.pokemon import PokemonFactory
#from engine.batterulogico import *

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
    x.a_iv = x.d_iv = 1
    x.hp_iv = 50
    x.health = 100
    if index < 3:
        team1.append(x)
    else:
        team2.append(x)


#battle(team1, team2)
