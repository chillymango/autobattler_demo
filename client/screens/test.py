import functools
import sys
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

from client.screens.context_window import Ui as ContextWindow
from utils.buttons import PokemonButton


class Ui(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('client/qtassets/test.ui', self)
        self.pushButton = self.findChild(QtWidgets.QPushButton, "pushButton")
        #self.pushButton.clicked.callback()
        self.context_window = ContextWindow()
        self.show()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print('Left Button Clicked')
        elif event.button() == QtCore.Qt.RightButton:
            print('Right button clicked')
            if True:
                # open a context window
                self.context_window.show()
                return
        self.context_window.hide()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
