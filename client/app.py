"""
Application Entrypoint
"""
import sys
from PyQt5 import QtWidgets
from PyQt5 import uic

from client.screens.user_name import Ui as UserNameUi
from client.utils.user import NoCachedUser
from client.utils.user import User

MATCH_ID = 'abcdefgh'


def error_window(msg):
    window = QtWidgets.QMessageBox()
    window.setWindowTitle('Encountered error')
    window.setText(msg)
    window.exec_()


class Ui(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('qtassets/landingscreen.ui', self)
        try:
            player = User.from_cache()
        except NoCachedUser:
            print('Could not find a cached player')
            # input player information
            self.window = UserNameUi()

        self.create_match = self.findChild(QtWidgets.QPushButton, 'createMatch')
        self.create_match.clicked.connect(self.create_match_callback)
        self.show()

    def create_match_callback(self):
        """
        eventually subscribe to lobby list and handle that
        """
        error_window('Create Match is not supported yet')

    def join_match(self):
        """
        join the only match that should ever be running
        """


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
