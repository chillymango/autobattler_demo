import os
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets


class RenderWindow(QtWidgets.QWidget):

    def __init__(self, path: str):
        """
        Path to the HTML file to render
        """
        super().__init__()
        if not os.path.exists(path):
            print('No render file found!')
            return

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create QWebView
        view = QtWebEngineWidgets.QWebEngineView()

        # load .html file
        view.load(QtCore.QUrl.fromLocalFile(os.path.abspath(path)))
        layout.addWidget(view)

        self.show()
