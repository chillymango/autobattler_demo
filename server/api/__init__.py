from .game import game_router
from .lobby import lobby_router


ALL_ROUTERS = [
    game_router,
    lobby_router
]


def add_routes(app):
    for router in ALL_ROUTERS:
        app.include_router(router)
