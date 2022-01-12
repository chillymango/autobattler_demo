import asyncio
import logging
import os
import sys
import time
from uuid import uuid4

from fastapi_websocket_pubsub import PubSubClient
from fastapi_websocket_pubsub import ALL_TOPICS
from fastapi_websocket_rpc.logger import logging_config, LoggingModes
from fastapi_websocket_rpc.logger import get_logger as rpc_get_logger

from server.api.player import Player as PlayerModel
from utils.client import GameServerClient

logging_config.set_mode(LoggingModes.UVICORN, level=logging.DEBUG)
logger = rpc_get_logger('ThisFuckingSucks')

sys.path.append(os.path.abspath(os.path.join(os.path.basename(__file__), "..")))

client = GameServerClient()
game = client.create_game()
p1 = PlayerModel(id=str(uuid4()), name='albert yang')
p2 = PlayerModel(id=str(uuid4()), name='brian yang')

client.join_game(game.game_id, p1)
client.join_game(game.game_id, p2)

client.start_game(game.game_id)


async def on_events(topic, data):
    logger.info(f'Received topic {topic}: {data}')

PORT = 8000
time.sleep(5.0)
async def main():
    # Create a client and subscribe to topics
    topic = f'pubsub-{game.game_id}'
    print('topic: {}'.format(topic))
    client = PubSubClient()
    #client.subscribe(topic, callback=on_events)
    client.subscribe(ALL_TOPICS, callback=on_events)
    print('subscribed')
    client.start_client("ws://localhost:8000/pubsub")
    print('started client')
    await client.wait_until_done()


asyncio.run(main())
