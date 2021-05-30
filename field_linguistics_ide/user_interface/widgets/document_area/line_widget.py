from collections import deque
from typing import Callable, Iterable
from contextlib import contextmanager
from PySide2 import QtGui, QtWidgets as Qt
from field_linguistics_ide.types_ import Line, Morpheme, Token
from field_linguistics_ide.user_interface.items import HSpacer
from field_linguistics_ide.user_interface.signals import Signal
from field_linguistics_ide.user_interface.widgets.document_area.common import EditableLabel, EditableWidgetsArea
from field_linguistics_ide.user_interface.widgets.document_area.token_widget import TokenWidget


class TranslationWidget(EditableWidgetsArea):
    def __init__(self, line: Line, document_area: 'DocumentArea'):
        self._document_area = document_area
        self.line = line
        self.text_widget = EditableLabel(line.translation)
        super().__init__()
        self.layout.addWidget(self.text_widget)

    def reset(self, line: Line):
        self.text_widget.setText(line.translation)

    def fixed_mode(self):
        self.text_widget.set_editable(False)

    def editable_mode(self):
        self.text_widget.set_editable(True)
        self._document_area.editing_translations.append(self)

    def focus_proxy_action(self):
        self.text_widget.focus_to_editable()

    def update(self, text: str):
        self.text_widget.update_fixed(text)
        self._document_area.document.update_translation(self.line.id_, text)

    def connect_editable_labels(self):
        self.text_widget.editable.textEdited.connect(self.update)


class AddTokenButton(Qt.QPushButton):
    def __init__(self, action: Callable):
        super().__init__('+')
        self.setSizePolicy(Qt.QSizePolicy.Minimum,
                           Qt.QSizePolicy.Minimum)
        self.setFixedWidth(30)
        self.pressed.connect(action)


class TokensLayout(Qt.QHBoxLayout):
    def __init__(self, token_widgets: Iterable[TokenWidget], add_token_action: Callable):
        super().__init__()
        self._add_token_action = add_token_action
        self._token_widgets = []
        self.spacer = HSpacer()
        self.add_token_button = AddTokenButton(self._add_token_action)
        deque(map(self.add_token, token_widgets), maxlen=0)
        self.addWidget(self.add_token_button)
        self.addItem(self.spacer)
        self.deleted_tokens = []

    @property
    def _token_index(self) -> int:
        return len(self._token_widgets)

    @contextmanager
    def _no_spacer_and_button(self):
        try:
            self.removeWidget(self.add_token_button)
            self.removeItem(self.spacer)
            yield
        finally:
            self.addWidget(self.add_token_button)
            self.addItem(self.spacer)

    def add_token(self, token_widget: TokenWidget):
        token_widget.index = self._token_index
        self._token_widgets.append(token_widget)
        self.addWidget(token_widget)

    def remove_token(self, token_id: int):
        for token_widget in self._token_widgets:
            if token_id:
                self.deleted_tokens.append(token_widget)
                self.removeWidget(token_widget)
                break

    def _show_tokens(self):
        tokens = []
        for i in range(self.count()):
            it = self.itemAt(i)
            if it is not None:
                w = it.widget()
                tokens.append(w)
        from pprint import pprint
        pprint(tokens)

    def _insert_token(self, position: int, token_widget: TokenWidget):
        new_token_widgets = []
        while self.count():
            widget_item = self.takeAt(0)
            if widget_item is not None:
                widget = widget_item.widget()
                new_token_widgets.append(widget)

        self._token_widgets = []
        for new_token_widget in new_token_widgets:
            self.add_token(new_token_widget)
            if self._token_index == position:
                self.add_token(token_widget)

    def insert_token(self, position: int, token_widget: TokenWidget):
        self._insert_token(position, token_widget)

    def add(self, position: int, token_widget: TokenWidget):
        with self._no_spacer_and_button():
            if position < 0:
                self.add_token(token_widget)
            else:
                self.insert_token(position, token_widget)


class LineWidget(Qt.QWidget):
    def __init__(self, line: Line, document_area: 'DocumentArea'):
        self.line = line
        self.document_area = document_area
        self.layout_contents = []
        super().__init__()
        self.line_layout = Qt.QVBoxLayout()
        self.spacer = HSpacer()
        self.tokens_layout = TokensLayout(self._create_tokens_widgets(line), self.add_token)
        self.line_layout.addLayout(self.tokens_layout)
        self.line_layout.addWidget(TranslationWidget(line, document_area))
        # empty line
        self.line_layout.addWidget(Qt.QLabel())
        self.setObjectName(f'line_widget{line.id_}')
        self.setLayout(self.line_layout)
        self.add_line = Signal()

    def _create_tokens_widgets(self, line: Line) -> Iterable[TokenWidget]:
        for token in line.tokens:
            token_widget = TokenWidget(token, self.document_area)
            token_widget.add_right.signal.connect(self.add_token)
            self.document_area.tokens_tray.update({token.id_: token_widget})
            yield token_widget

    def add_token(self, position: int = -1):
        token = Token([])
        morpheme = Morpheme('', '', is_stem=True)
        self.document_area.document.add_morpheme_to_token(morpheme, token)
        self.document_area.document.add_token_to_line(token, self.line, position=position)
        token_widget = TokenWidget(token, self.document_area)
        self.document_area.tokens_tray.update({token.id_: token_widget})
        token_widget.add_right.signal.connect(self.add_token)
        self.tokens_layout.add(position, token_widget)
        self.dumpObjectTree()

    def closeEvent(self, _):
        self.document_area.lines_tray.pop(self.line.id_)
        self.document_area.document.pop_line(self.line.id_)

    def contextMenuEvent(self, menu_event: QtGui.QContextMenuEvent):
        menu: Qt.QMenu = Qt.QMenu()
        add_action = Qt.QAction('Add new')
        add_action.setText('Add new')
        add_action.triggered.connect(self.add_line.signal.emit)
        menu.addAction(add_action)
        delete_action = Qt.QAction('Delete')
        delete_action.setText('Delete')
        delete_action.triggered.connect(self.close)
        menu.addAction(delete_action)
        menu.exec_(menu_event.globalPos())
        menu.deleteLater()
