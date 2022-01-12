"""
Pubsub interface for the game

Supports broadcasting game state
"""
import asyncio
import time
import typing as T

from engine.base import Component

UPDATE_FREQUENCY = 10.0  # hz


class PubSubInterface(Component):

    def initialize(self):
        super().initialize()
        # do some stuff here to start broadcasting on the correct channels
        # use game ID for namespace
        self._pubsub_header = f"pubsub-{self.env.id}"
        print(f"PubSub on {self._pubsub_header}")

        # NOTE: defer import to break circular deps
        from server.api.pubsub import endpoint
        self.endpoint = endpoint

        self.task = asyncio.create_task(self.broadcast())
        print('Created the loop')

    async def broadcast(self):
        print("Doing the thing now")
        while True:
            await self.endpoint.publish(self._pubsub_header, self.state.json())
            await asyncio.sleep(1.0 / UPDATE_FREQUENCY)

    def cleanup(self):
        """
        Stop broadcasting updates
        """
        self.task.cancel()
