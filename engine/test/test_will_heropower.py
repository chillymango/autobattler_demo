from engine.env import Environment
from engine.models.player import Player
from engine.models.hero import NORMAL_HEROES
from engine.models.hero import Hero

HEROES = NORMAL_HEROES
heroes = [x for x in HEROES]
env = Environment.create_webless_game(4)
p1 = Player(name='bassf s')
env.add_player(p1)
env.state.player_hero[str(p1.id)] = heroes[-1]
heroes[1].set_env(env)
p1.hitpoints = 20
env.state.player_hero[p1.id]._power.turn_setup()
env.state.player_hero[p1.id]._power.immediate_action(p1)
