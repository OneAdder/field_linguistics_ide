from PySide2 import QtWidgets as Qt
from field_linguistics_ide.user_interface.widgets.common import Signal


class MainArea(Qt.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tab_closed = Signal()
        self.tabCloseRequested.connect(self.close_tab)

    def close_tab(self, current_index):
        current_widget = self.widget(current_index)
        current_widget.close()
        self.tab_closed.signal.emit()
        self.removeTab(current_index)

    # def tabCloseRequested(self, *args, **kwargs):
    #     print()
