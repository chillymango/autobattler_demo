"""
Just for testing the window
"""
import asyncio
import os
import sys

from asyncqt import QEventLoop
from fastapi_websocket_pubsub import PubSubClient
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                             QToolTip, QMessageBox, QLabel)

PORT = int(os.environ.get("PORT") or "8000")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "First Window"
        self.top = 100
        self.left = 100
        self.width = 680
        self.height = 500

        self.pushButton = QPushButton("Start", self)
        self.pushButton.move(275, 200)
        self.pushButton.setToolTip("<h3>Start the Session</h3>")

        self.testLabel = QLabel("testLabel", self)
        self.testLabel.move(400, 200)
        self.testLabel.setText("testing only")

        self.client = PubSubClient()
        self.client.subscribe("state", self.on_data)
        self.main_window()
        self.client.start_client(f"ws://localhost:{PORT}/pubsub")

    def main_window(self):
        self.label = QLabel("Manager", self)
        self.label.move(285, 175)
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)
        self.show()

    async def on_data(self, data, topic):
        """
        YADDA
        """
        print("Topic: {}".format(topic))
        print("Data: {}".format(data))
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = Window()
    with loop:
        loop.run_forever()
    #sys.exit(app.exec())
