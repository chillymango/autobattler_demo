import sys
import asyncio

from PyQt5 import QtCore, QtWidgets
from asyncqt import QEventLoop

from speedometer import Speedometer
from server import UDPserver


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.spd = Speedometer()
        self.spinBox = QtWidgets.QSpinBox()
        self.spinBox.setRange(0, 359)
        self.spinBox.valueChanged.connect(lambda value: self.spd.setAngle(value))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.spd)
        layout.addWidget(self.spinBox)

    @QtCore.pyqtSlot(float, float, float, float)
    def set_data(self, east_coord, north_coord, veh_speed, ag_yaw):
        print(east_coord, north_coord, veh_speed, ag_yaw)
        self.spd.setAngle(veh_speed)


async def create_server(loop):
    return await loop.create_datagram_endpoint(
        lambda: UDPserver(), local_addr=("127.0.0.1", 20002)
    )


def main():
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = Widget()
    w.resize(640, 480)
    w.show()

    with loop:
        _, protocol = loop.run_until_complete(create_server(loop))
        protocol.dataChanged.connect(w.set_data)
        loop.run_forever()


if __name__ == "__main__":
    main()