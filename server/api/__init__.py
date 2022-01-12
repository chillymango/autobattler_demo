from .game import game_router
from .lobby import lobby_router
from .pubsub import pubsub_router

ALL_ROUTERS = [
    game_router,
    lobby_router,
    pubsub_router
]


def add_routes(app):
    for router in ALL_ROUTERS:
        app.include_router(router)
