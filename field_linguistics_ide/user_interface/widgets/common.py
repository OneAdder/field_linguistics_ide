from PySide2 import QtCore, QtWidgets as Qt


class ScrollArea(Qt.QScrollArea):
    def __init__(self,):
        super().__init__()
        content_widget = Qt.QWidget()
        self.setWidget(content_widget)
        # layout inside the scroll area
        self.flay = Qt.QVBoxLayout(content_widget)
        self.setWidgetResizable(True)


class Signal(QtCore.QObject):
    signal = QtCore.Signal()


class IntSignal(QtCore.QObject):
    signal = QtCore.Signal(int)


class BoolSignal(QtCore.QObject):
    signal = QtCore.Signal(bool)


class StrSignal(QtCore.QObject):
    signal = QtCore.Signal(str)
