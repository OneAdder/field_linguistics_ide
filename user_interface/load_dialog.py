from pathlib import Path
from PySide2 import QtWidgets as Qt
from field_linguistics_ide.user_interface.widgets.common import Signal, StrSignal


class ProjectDialog(Qt.QDialog):
    def __init__(self):
        super().__init__()
        layout = Qt.QVBoxLayout()
        self.create_button = Qt.QPushButton('Create')
        self.create_signal = Signal()
        self.create_button.pressed.connect(self.create_project)
        layout.addWidget(self.create_button)
        self.load_button = Qt.QPushButton('Load')
        self.load_signal = StrSignal()
        self.load_button.pressed.connect(self.load_project)
        layout.addWidget(self.load_button)
        self.setLayout(layout)
        self._no_actions_close = True

    def closeEvent(self, event):
        if self._no_actions_close:
            self.create_signal.signal.emit()
        super().closeEvent(event)

    def create_project(self):
        self.create_signal.signal.emit()
        self._no_actions_close = False
        self.close()

    def load_project(self):
        directory = Qt.QFileDialog.getExistingDirectory(
            self, 'Import', str(Path.home()))
        try:
            self.load_signal.signal.emit(directory)
            self._no_actions_close = False
            self.close()
        except FileNotFoundError:
            pass
