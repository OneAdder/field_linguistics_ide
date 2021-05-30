from PySide2 import QtCore


class Signal(QtCore.QObject):
    signal = QtCore.Signal()


class IntSignal(QtCore.QObject):
    signal = QtCore.Signal(int)


class BoolSignal(QtCore.QObject):
    signal = QtCore.Signal(bool)


class StrSignal(QtCore.QObject):
    signal = QtCore.Signal(str)
