"""
Pubsub interface for the game

Supports broadcasting game state
"""
import asyncio
import time
import typing as T
from queue import Empty
from queue import Queue
from pydantic import BaseModel
from pydantic import Field

from engine.base import Component
from engine.player import Player

UPDATE_FREQUENCY = 10.0  # hz


__ALL_PLAYERS__ = "__ALL_PLAYERS_CONSTANT__"


class Message(BaseModel):

    msg: str
    time: float = Field(default_factory=time.time)


class PubSubInterface(Component):

    def initialize(self):
        super().initialize()
        # do some stuff here to start broadcasting on the correct channels
        # use game ID for namespace

        self.message_player_queue = {player: Queue() for player in self.state.players}
        self.message_global_queue = Queue()

        # broadcast state
        self._pubsub_state_header = f"pubsub-state-{self.env.id}"
        print(f"PubSub state on {self._pubsub_state_header}")

        # broadcast global messages (all players)
        self._pubsub_msg_global_header = f"pubsub-msg-all-{self.env.id}"
        print(f"PubSub msg all on {self._pubsub_msg_global_header}")

        # broadcast specific player messages
        self._pubsub_msg_headers = {}
        for player in self.state.players:
            self._pubsub_msg_headers[player] = f"pubsub-msg-{str(player.id)}-{self.env.id}"
            print(f"PubSub msg player {player.name} on {self._pubsub_msg_headers[player]}")

        # NOTE: defer import to break circular deps
        from server.api.pubsub import endpoint
        self.endpoint = endpoint

        self.task = asyncio.create_task(self.broadcast())
        print('Created the loop')

    async def broadcast(self):
        print("Doing the thing now")
        while True:
            # broadcast encoded state
            print('looping')
            await self.endpoint.publish(self._pubsub_state_header, self.state.json())
            print('published state')
            # broadcast any new messages from message queue
            tasks = [self._flush_global_messages()] + [
                self._flush_player_messages(p) for p in self.state.players
            ]
            print(tasks)

            await asyncio.gather(*tasks, return_exceptions=True)
            #await asyncio.gather(*tasks)

            await asyncio.sleep(1.0 / UPDATE_FREQUENCY)

    async def _flush_global_messages(self):
        """
        Flush the message queue for global
        """
        while True:
            try:
                item = self.message_global_queue.get_nowait()
                if not isinstance(item, Message):
                    # drop the message and print a loud warning
                    print(f"Message dispatch received invalid item:\n\t{item}")
                encoded = item.json()
                await self.endpoint.publish(self._pubsub_msg_global_header, encoded)
            except Empty:
                break
            except Exception as exc:
                print(f'Exception in flush g messages: {repr(exc)}')

    async def _flush_player_messages(self, player: Player):
        """
        Flush the message queue for a player
        """
        header = self._pubsub_msg_headers[player]
        queue = self.message_player_queue[player]
        while True:
            try:
                await self.endpoint.publish(header, queue.get_nowait())
            except Empty:
                break
            except Exception as exc:
                print(f'Exception in flush p messages: {repr(exc)}')

    def log(self, message: Message, recipient: T.Union[T.List[Player], Player]=__ALL_PLAYERS__):
        if recipient == __ALL_PLAYERS__:
            self.message_global_queue.put(message)
        if isinstance(recipient, Player):
            recipient = [recipient]
        for player in recipient:
            self.message_player_queue[player].put(message)


    def cleanup(self):
        """
        Stop broadcasting updates
        """
        self.task.cancel()
