import asyncio
import os
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from utils.websockets_client import WebSocketClient


class RenderWindow(QtWidgets.QWidget):

    POST_BATTLE_DURATION = 10.0

    def __init__(
        self,
        parent: QtWidgets.QMainWindow,
        path: str,
        websocket = None,
        post_battle_duration: float = None,
    ):
        """
        Path to the HTML file to render
        """
        super().__init__()
        self.websocket: WebSocketClient = websocket
        self.path = path
        if post_battle_duration is not None:
            self.POST_BATTLE_DURATION = post_battle_duration

        self.parent = parent
        self.closing = False
        if not os.path.exists(path):
            print('No render file found!')
            return

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create QWebView
        self.view = QtWebEngineWidgets.QWebEngineView()

        # load .html file
        self.view.load(QtCore.QUrl.fromLocalFile(os.path.abspath(path)))
        layout.addWidget(self.view)

        # setup a callback that closes this window if the battle has been concluded for 10s

        for callback in [
            self.check_battle_render_state
        ]:
            timer = QtCore.QTimer(self)
            timer.timeout.connect(callback)
            timer.start(100)

        self.show()

    def on_battle_finish(self, finished: bool):
        if not finished:
            return
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.close_wrapper)
        timer.setSingleShot(True)
        timer.start(self.POST_BATTLE_DURATION * 1000)
        self.closing = True

    def check_battle_render_state(self):
        if self.closing:
            return
        self.view.findText("won", resultCallback=self.on_battle_finish)

    def close_wrapper(self):
        self.close()

    def closeEvent(self, *args, **kwargs):
        asyncio.ensure_future(self.websocket.finish_rendering_battle(self.parent.context))
        self.parent.render_window = None
        super().closeEvent(*args, **kwargs)
