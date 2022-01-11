import asyncio

from PyQt5 import QtCore


class UDPserver(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._transport = None
        self._counter_message = 0

    @property
    def transport(self):
        return self._transport

    def connection_made(self, transport):
        self._transport = transport

    def datagram_received(self, data, addr):
        self._counter_message += 1
        print("#Num of Mssg Received: {}".format(self._counter_message))
        message = data.decode()
        east_coord_str, north_coord_str, veh_speed_str, ag_yaw_str, *_ = message.split(
            "/"
        )
        try:
            east_coord = float(east_coord_str)
            north_coord = float(north_coord_str)
            veh_speed = float(veh_speed_str)
            ag_yaw = float(ag_yaw_str)
            self.dataChanged.emit(east_coord, north_coord, veh_speed, ag_yaw)
        except ValueError as e:
            print(e)
