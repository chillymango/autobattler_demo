from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
import sys
import os

# Create application
app = QtWidgets.QApplication(sys.argv)

# Add window
win = QtWidgets.QWidget()
win.setWindowTitle('BATTLE PALACE ANIMATED')

# Add layout
layout = QtWidgets.QVBoxLayout()
win.setLayout(layout)

# Create QWebView
view = QtWebEngineWidgets.QWebEngineView()

# load .html file
view.load(QtCore.QUrl.fromLocalFile(os.path.abspath('fastbattle.html')))
layout.addWidget(view)

win.show()
app.exec_()