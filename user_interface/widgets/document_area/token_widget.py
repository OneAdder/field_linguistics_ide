from typing import Iterable, Optional
from PySide2 import QtCore, QtGui, QtWidgets as Qt
from field_linguistics_ide.types_ import Morpheme, Token
from field_linguistics_ide.user_interface.widgets.common import Signal, IntSignal
from field_linguistics_ide.user_interface.widgets.document_area.common import Tray
from field_linguistics_ide.user_interface.widgets.document_area.morpheme_widget import MorphemeWidget


class TokenWidget(Qt.QGroupBox):
    def __init__(self, token: Token, document_area: 'DocumentArea'):
        self.index: Optional[int] = None
        self.token = token
        self.document_area = document_area
        self.morphemes_tray = Tray()
        super().__init__()
        self.layout = Qt.QHBoxLayout()
        self.layout.setSpacing(1)
        for morpheme_widget in self._create_morpheme_widgets():
            document_area.morphemes_tray.update(
                {morpheme_widget.morpheme.id_: morpheme_widget}
            )
            self.layout.addWidget(morpheme_widget)
        self.setLayout(self.layout)
        # self.closed.connect(p)
        self.add_right = IntSignal()

    def _create_morpheme_widgets(self) -> Iterable[MorphemeWidget]:
        for morpheme_index, morpheme in enumerate(self.token.morphemes):
            morpheme_widget = MorphemeWidget(morpheme, self.document_area)
            morpheme_widget.index = morpheme_index
            morpheme_widget.split.signal.connect(
                lambda pos: self.split_morpheme(morpheme_widget, pos)
            )
            yield morpheme_widget

    def __repr__(self):
        return '{cls}(index={index}, token={token})'.format(
            cls=type(self).__name__, index=self.index, token=self.token)

    def closeEvent(self, _):
        self.document_area.document.pop_token(self.token.id_)
        super().close()

    def insert_morpheme(self, position: int, widget: MorphemeWidget):
        self.layout.insertWidget(position, widget)

    def reindex(self):
        widgets = []
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            widgets.append(widget)
        for widget in widgets:
            self.layout.addWidget(widget)

    def split_morpheme(self, morpheme_widget: MorphemeWidget, split_position: int):
        text = morpheme_widget.text()
        morpheme = morpheme_widget.morpheme
        morpheme.text = text[:split_position]
        morpheme_widget.reset(morpheme)
        new_morpheme = Morpheme(text[split_position:], None)
        self.document_area.document.add_morpheme_to_token(
            new_morpheme, self.token, position=morpheme_widget.index+1)
        self.document_area.morphemes_tray.update({morpheme_widget.morpheme.id_: morpheme_widget})
        new_morpheme_widget = MorphemeWidget(new_morpheme, self.document_area)
        self.insert_morpheme(morpheme_widget.index+1, new_morpheme_widget)
        self.reindex()

    def contextMenuEvent(self, menu_event: QtGui.QContextMenuEvent):
        menu = Qt.QMenu()
        action_add_right = Qt.QAction('Add token')
        action_add_right.setText('Add token')
        action_add_right.triggered.connect(lambda: self.add_right.signal.emit(self.index + 1))
        menu.addAction(action_add_right)
        action_delete = Qt.QAction('Delete token')
        action_delete.setText('Delete token')
        action_delete.triggered.connect(self.close)
        menu.addAction(action_delete)
        menu.exec_(menu_event.globalPos())
        menu.deleteLater()
