from typing import Any
from PySide2 import QtCore, QtGui, QtWidgets as Qt
from field_linguistics_ide.user_interface.widgets.dictionary_area import DictionaryArea


class Tray(dict):
    def pop(self, key):
        self[key].deleteLater()
        super().pop(key)


class EditableLabel(Qt.QWidget):
    def __init__(self, text: str):
        self._dictionary = DictionaryArea.get_instance()
        super().__init__()
        layout = Qt.QHBoxLayout()
        self.fixed = Qt.QLabel(text)
        self.editable = Qt.QLineEdit(text)
        # self.editable.contextMenuEvent = self.contextMenuEvent
        self.editable.setSizePolicy(Qt.QSizePolicy.Minimum,
                                    Qt.QSizePolicy.Preferred)
        self.editable.setHidden(True)
        # self.editable.createStandardContextMenu()
        layout.addWidget(self.fixed)
        layout.addWidget(self.editable)
        self.setLayout(layout)

    def update_fixed(self, new_text: str):
        self.fixed.setText(new_text)

    def focus_to_editable(self):
        self.editable.setFocus()

    def set_editable(self, editable: bool):
        if editable:
            self.fixed.setHidden(True)
            self.editable.setHidden(False)
        else:
            self.fixed.setHidden(False)
            self.editable.setHidden(True)

    def setText(self, text: str):
        self.fixed.setText(text)
        self.editable.setText(text)

    def text(self):
        return self.editable.text()


class EditableWidgetsArea(Qt.QWidget):
    SPACING = 1

    def __init__(self):
        super().__init__()
        self.is_editable = False
        self.layout = Qt.QVBoxLayout()
        self.setLayout(self.layout)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.connect_editable_labels()

    def focusInEvent(self, _):
        self.setStyleSheet('background: gray;')

    def focusOutEvent(self, _):
        self.setStyleSheet('')

    def reset(self, data: Any):
        pass

    def _fixed_mode(self):
        pass

    def fixed_mode(self):
        if self.is_editable:
            self._fixed_mode()
            self.is_editable = False

    def _editable_mode(self):
        pass

    def editable_mode(self):
        if not self.is_editable:
            self._editable_mode()
            self.is_editable = True

    def focus_proxy_action(self):
        pass

    def mouseDoubleClickEvent(self, _):
        self.editable_mode()

    def delete_action(self):
        pass

    def keyPressEvent(self, key_event: QtGui.QKeyEvent):
        key = key_event.key()
        if key == QtCore.Qt.Key_Right:
            self.fixed_mode()
            self.focusNextChild()
        elif key == QtCore.Qt.Key_Left:
            self.fixed_mode()
            self.focusPreviousChild()
        elif key == QtCore.Qt.Key_Return:
            if self.is_editable:
                self.focus_proxy_action()
                self.text_widget.focus_to_editable()
            else:
                self.editable_mode()
        elif key == QtCore.Qt.Key_Escape:
            self.fixed_mode()
            self.setFocus()
        elif key == QtCore.Qt.Key_Delete:
            self.delete_action()

    def connect_editable_labels(self):
        pass
