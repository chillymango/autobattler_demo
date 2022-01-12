"""
Pubsub interface for the game

Supports broadcasting game state
"""
import typing as T

from fastapi import APIRouter
from fastapi_websocket_pubsub import PubSubEndpoint

pubsub_router = APIRouter(prefix="/pubsub")

endpoint = PubSubEndpoint()
endpoint.register_route(pubsub_router)

print('This module was imported')