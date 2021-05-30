from PySide2 import QtWidgets as Qt


class ScrollArea(Qt.QScrollArea):
    def __init__(self,):
        super().__init__()
        content_widget = Qt.QWidget()
        self.setWidget(content_widget)
        # layout inside the scroll area
        self.flay = Qt.QVBoxLayout(content_widget)
        self.setWidgetResizable(True)
