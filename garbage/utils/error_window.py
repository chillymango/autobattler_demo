from PyQt5 import QtWidgets


def error_window(msg):
    window = QtWidgets.QMessageBox()
    window.setWindowTitle('Encountered error')
    window.setText(msg)
    window.exec_()
