from uuid import uuid4

from utils.client import GameServerClient
from api.player import Player as PlayerModel

client = GameServerClient()
game = client.create_game()
player = PlayerModel(id=str(uuid4()), name='albert yang')
client.join_game(game.game_id, player)
print(client.get_players(game.game_id))
client.leave_game(game.game_id, player)
print(client.get_players(game.game_id))
try:
    client.leave_game(game.game_id, player)
    print('ok that should have failed wyd')
except:
    print('ok nice that wasnt supposed to work and it didnt')
