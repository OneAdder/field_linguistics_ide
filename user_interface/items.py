from PySide2 import QtWidgets as Qt


class HSpacer(Qt.QSpacerItem):
    def __init__(self):
        super().__init__(40, 20,
                         Qt.QSizePolicy.Expanding,
                         Qt.QSizePolicy.Minimum)


class VSpacer(Qt.QSpacerItem):
    def __init__(self):
        super().__init__(20, 40,
                         Qt.QSizePolicy.Minimum,
                         Qt.QSizePolicy.Expanding)
