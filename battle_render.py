import threading
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from qasync import QEventLoop
from threading import Thread
import asyncio
import sys
import os

path = "Bruno_Preschooler_1.html"
# Create application
app = QtWidgets.QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Add window
win = QtWidgets.QWidget()
win.setWindowTitle('BATTLE PALACE ANIMATED')

# Add layout
layout = QtWidgets.QVBoxLayout()
win.setLayout(layout)

# Create QWebView
view = QtWebEngineWidgets.QWebEngineView()

# load .html file
view.load(QtCore.QUrl.fromLocalFile(os.path.abspath(path)))
layout.addWidget(view)

async def check_if_view_has_text(view: QtWebEngineWidgets.QWebEngineView):
    def callback(val: bool):
        if val:
            print('I was found')
            timer = QtCore.QTimer(app)
            timer.timeout.connect(win.close)
            timer.start(10000)
        else:
            print('I was not found')

    while True:
        await asyncio.sleep(1.0)
        view.findText("won", resultCallback=callback)


win.show()
loop.run_until_complete(check_if_view_has_text(view))
#coro = check_if_view_has_text(view)
#loop.run_until_complete(coro)

#win.show()
#thread = Thread(target=check_if_view_has_text, args=(view, ))
#thread.daemon = True
#thread.start()
