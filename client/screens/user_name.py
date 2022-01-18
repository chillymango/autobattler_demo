"""
Screen should prompt a user to provide their name
"""
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

from server.api.user import User


class Ui(QtWidgets.QDialog):

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('client/qtassets/nameprompt.ui', self)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        self.name_submitted = False
        self.submit_name = self.findChild(QtWidgets.QPushButton, "submit")
        self.submit_name.clicked.connect(self.submit_name_callback)
        self.show()

    def submit_name_callback(self):
        first_name = self.findChild(QtWidgets.QLineEdit, "firstName").text()
        last_name = self.findChild(QtWidgets.QLineEdit, "lastName").text()
        player = User(name=f'{first_name} {last_name}')
        print('Created a player {} with id {}'.format(player.name, player.id))
        player.to_cache()
        self.name_submitted = True

