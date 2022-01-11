from PyQt5 import QtCore, QtGui, QtWidgets


class Speedometer(QtWidgets.QWidget):
    angleChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._angle = 0.0

        self._margins = 20

        self._pointText = {
            0: "40",
            30: "50",
            60: "60",
            90: "70",
            120: "80",
            150: "",
            180: "",
            210: "",
            240: "0",
            270: "10",
            300: "20",
            330: "30",
            360: "",
        }

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.fillRect(event.rect(), self.palette().brush(QtGui.QPalette.Window))
        self.drawMarkings(painter)
        self.drawNeedle(painter)

    def drawMarkings(self, painter):

        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        scale = min(
            (self.width() - self._margins) / 120.0,
            (self.height() - self._margins) / 60.0,
        )
        painter.scale(scale, scale)

        font = QtGui.QFont(self.font())
        font.setPixelSize(10)
        metrics = QtGui.QFontMetricsF(font)

        painter.setFont(font)
        painter.setPen(self.palette().color(QtGui.QPalette.Shadow))

        i = 0

        while i < 360:

            if i % 30 == 0 and (i < 150 or i > 210):
                painter.drawLine(0, -40, 0, -50)
                painter.drawText(
                    -metrics.width(self._pointText[i]) / 2.0, -52, self._pointText[i]
                )
            elif i < 135 or i > 225:
                painter.drawLine(0, -45, 0, -50)

            painter.rotate(15)
            i += 15

        painter.restore()

    def drawNeedle(self, painter):

        painter.save()
        painter.translate(self.width() / 2, self.height() / 1.5)
        painter.rotate(self._angle)
        scale = min(
            (self.width() - self._margins) / 120.0,
            (self.height() - self._margins) / 120.0,
        )
        painter.scale(scale, scale)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.palette().brush(QtGui.QPalette.Shadow))

        painter.drawPolygon(
            QtGui.QPolygon(
                [
                    QtCore.QPoint(-10, 0),
                    QtCore.QPoint(0, -45),
                    QtCore.QPoint(10, 0),
                    QtCore.QPoint(0, 5),
                    QtCore.QPoint(-10, 0),
                ]
            )
        )

        painter.setBrush(self.palette().brush(QtGui.QPalette.Highlight))

        painter.drawPolygon(
            QtGui.QPolygon(
                [
                    QtCore.QPoint(-5, -25),
                    QtCore.QPoint(0, -45),
                    QtCore.QPoint(5, -25),
                    QtCore.QPoint(0, -30),
                    QtCore.QPoint(-5, -25),
                ]
            )
        )

        painter.restore()

    def sizeHint(self):

        return QtCore.QSize(150, 150)

    def angle(self):
        return self._angle

    @QtCore.pyqtSlot(float)
    def setAngle(self, angle):

        if angle != self._angle:
            self._angle = angle
            self.angleChanged.emit(angle)
            self.update()

    angle = QtCore.pyqtProperty(float, angle, setAngle)


if __name__ == "__main__":
    import sys
    import asyncio
    from asyncqt import QEventLoop

    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        w = Speedometer()
        w.angle = 10
        w.show()
        loop.run_forever()