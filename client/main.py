"""
Client Entrypoint

The game should load from this script.

Steps:
First checks to see if the User object can be instantiated from cache.
    If it cannot, prompt the user to create one by using the user prompt window.
"""
import asyncio
import logging
import sys
import typing as T
from collections import namedtuple

from fastapi_websocket_rpc.logger import logging_config
from fastapi_websocket_rpc.logger import LoggingModes
from PyQt5 import QtWidgets
from qasync import QEventLoop

from client.screens.landing_window import Ui as LandingWindow
from client.screens.user_name import Ui as UserNameWindow
from utils.client import AsynchronousServerClient
from utils.server_config import ServerConfig
from server.api.user import NoCachedUser
from server.api.user import User

#logging_config.set_mode(LoggingModes.UVICORN, level=logging.DEBUG)
logging_config.set_mode(LoggingModes.UVICORN, level=logging.WARNING)

WindowTransition = namedtuple("WindowTransition", ["before", "after"])


class WindowManager:
    """
    State machine management class.
    """

    def __init__(self):
        # load server configuration and create clients

        # define the window orders
        self.window_transitions = [
            WindowTransition(UserNameWindow, LandingWindow),
            #WindowTransition(LandingWindow, CreateGameWindow),
            #WindowTransition(CreateGameWindow, LobbyWindow),
            #WindowTransition(LandingWindow, JoinGameWindow),
            #WindowTransition(LobbyWindow, BattleWindow),
            #WindowTransition(BattleWindow, LandingWindow),
        ]

        self.current_window = None


async def user_name_window():
    """
    Check if a user can be created.

    If a user already exists, return that user.
    If a user does not already exist, open a window to prompt the player to enter info.
    """
    try:
        user = User.from_cache()
    except NoCachedUser:
        window = UserNameWindow()
        while not window.name_submitted:
            await asyncio.sleep(1.0)
        user = User.from_cache()

    return user


async def main() -> None:
    """
    Application Entrypoint
    """
    server_config = ServerConfig.parse_filepath()
    client = AsynchronousServerClient(bind=server_config.bind)
    window = LandingWindow(client, server_config)
    user = await user_name_window()
    print(f'Found User {user}')
    window.set_user(user)
    # TODO: what do i do here lol... the rest of the machine is probably self contained
    while True:
        await asyncio.sleep(0.0)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    loop.set_debug(True)
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    #loop.run_forever()