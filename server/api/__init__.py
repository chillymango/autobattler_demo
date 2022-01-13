from .debug import debug_router
from .game import game_router
from .lobby import lobby_router
from .pubsub import pubsub_router
from .shop import shop_router

ALL_ROUTERS = [
    debug_router,
    game_router,
    lobby_router,
    pubsub_router,
    shop_router
]


def add_routes(app):
    for router in ALL_ROUTERS:
        app.include_router(router)
