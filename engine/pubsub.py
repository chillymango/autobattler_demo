"""
Pubsub interface for the game

Supports broadcasting game state
"""
import asyncio
import typing as T
from queue import Empty

from engine.base import Component
from engine.logger import Logger, Message
from engine.player import Player

if T.TYPE_CHECKING:
    from engine.env import Environment
    from engine.models.state import State

UPDATE_FREQUENCY = 10.0  # hz


class PubSubInterface(Component):

    def initialize(self):
        super().initialize()
        # assumes the logger component is set up first
        self.logger: Logger = self.env.logger

        # increase broadcast speed
        self.update_freq = 10.0

        # do some stuff here to start broadcasting on the correct channels
        # use game ID for namespace
        for player in self.state.players:
            self._pubsub_msg_headers[player] = f"pubsub-msg-{str(player.id)}-{self.env.id}"
            print(f"PubSub msg player {player.name} on {self._pubsub_msg_headers[player]}")

    def __init__(self, env: "Environment", state: "State"):
        super().__init__(env, state)
        # specific player messages
        self._pubsub_msg_headers = {}
        # broadcast global messages (all players)
        self._pubsub_msg_global_header = f"pubsub-msg-all-{self.env.id}"
        print(f"PubSub msg all on {self._pubsub_msg_global_header}")

        self.update_freq = 1.0
        self._pubsub_state_header = f"pubsub-state-{self.env.id}"
        print(f"PubSub state on {self._pubsub_state_header}")

        # NOTE: defer import to break circular deps
        from server.api.pubsub import endpoint
        self.endpoint = endpoint

        self.task = asyncio.create_task(self.broadcast())
        print('Created the loop')

    async def broadcast(self):
        print("Doing the thing now")
        while True:
            # broadcast encoded state
            await self.endpoint.publish(self._pubsub_state_header, self.state.json())
            # broadcast any new messages from message queue
            tasks = [self._flush_global_messages()] + [
                self._flush_player_messages(p) for p in self.state.players
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(1.0 / self.update_freq)

    async def _flush_queue(self, topic, queue):
        """
        Flush a queue of Message objects
        """
        while True:
            try:
                item = queue.get_nowait()
                if not isinstance(item, Message):
                    # drop the message and print a loud warning
                    print(f'Message dispatch received invalid item:\n\t{item}')
                print(f'Queue receives {item}')
                encoded = item.json()
                await self.endpoint.publish(topic, encoded)
            except Empty:
                break
            except Exception as exc:
                print(f'Exception in flushing messages: {repr(exc)}')
                raise

    async def _flush_global_messages(self):
        """
        Flush the message queue for global
        """
        header = self._pubsub_msg_global_header
        queue=self.logger.message_global_queue
        await self._flush_queue(
            topic=header,
            queue=queue,
        )

    async def _flush_player_messages(self, player: Player):
        """
        Flush the message queue for a player
        """
        header = self._pubsub_msg_headers[player]
        queue = self.logger.message_player_queue[player]
        await self._flush_queue(topic=header, queue=queue)

    def cleanup(self):
        """
        Stop broadcasting updates
        """
        self.task.cancel()
