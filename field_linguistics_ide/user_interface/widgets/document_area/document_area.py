from collections import deque
from typing import Callable, Deque, Optional, Tuple
from contextlib import contextmanager
from PySide2 import QtGui, QtWidgets as Qt

from field_linguistics_ide.types_ import Document, Line, Morpheme, Token
from field_linguistics_ide.user_interface.items import VSpacer
from field_linguistics_ide.user_interface.signals import Signal
from field_linguistics_ide.user_interface.widgets.common import ScrollArea
from field_linguistics_ide.user_interface.widgets.dictionary_area import DictionaryArea
from field_linguistics_ide.user_interface.widgets.document_area.common import Tray
from field_linguistics_ide.user_interface.widgets.document_area.morpheme_widget import MorphemeWidget
from field_linguistics_ide.user_interface.widgets.document_area.line_widget import LineWidget, TranslationWidget


class AddLineButton(Qt.QPushButton):
    def __init__(self, action: Callable):
        super().__init__('+')
        self.setSizePolicy(Qt.QSizePolicy.Minimum,
                           Qt.QSizePolicy.Minimum)
        self.setFixedHeight(30)
        self.setFixedWidth(200)
        self.pressed.connect(action)


class DocumentArea(ScrollArea):
    def __init__(self, document: Document):
        self.dictionary_area = DictionaryArea.get_instance()
        super().__init__()
        self.lines_tray = Tray()
        self.tokens_tray = Tray()
        self.morphemes_tray = Tray()
        self.document = document
        self.editing_morphemes: Deque[MorphemeWidget] = deque()
        self.editing_translations: Deque[TranslationWidget] = deque()
        self.deleted_morphemes: Deque[Tuple[int, int, Morpheme]] = deque()
        self.spacer = VSpacer()
        self.add_line_button = AddLineButton(self.add_line)
        Qt.QShortcut(QtGui.QKeySequence("Ctrl+z"), self, self.ctrl_z_action)
        self.update_signal = Signal()

    def display(self):
        line_index = 0
        for line in self.document.data:
            line_widget = LineWidget(line, self)
            line_widget.add_line.signal.connect(self.add_line)
            self.lines_tray.update({line.id_: line_widget})
            # add to the grid in the scroll area
            self.flay.addWidget(line_widget)
            line_index += 1
        self.flay.addWidget(self.add_line_button)
        # spacer at the end of the layout to prevent stretching
        self.flay.addItem(self.spacer)

    def stop_editing(self):
        while self.editing_morphemes:
            self.editing_morphemes.pop().fixed_mode()
        while self.editing_translations:
            self.editing_translations.pop().fixed_mode()

    def mousePressEvent(self, _):
        self.stop_editing()
        self.update_signal.signal.emit()

    def ctrl_z_action(self):
        if not self.deleted_morphemes:
            return
        morpheme_data = self.deleted_morphemes.pop()
        morpheme_widget = MorphemeWidget.from_deleted(*morpheme_data, self)
        token_id, position, morpheme = morpheme_data
        self.morphemes_tray.update({morpheme.id_: morpheme_widget})
        self.tokens_tray[token_id].insert_widget(position, morpheme_widget)

    @contextmanager
    def _no_spacer_and_add_button(self):
        try:
            self.flay.removeWidget(self.add_line_button)
            self.flay.removeItem(self.spacer)
            yield
        finally:
            self.flay.addWidget(self.add_line_button)
            self.flay.addItem(self.spacer)

    def add_line(self):
        line = Line.new(self.document)
        line.translation = '?'
        self.document.add_line(line)
        line_widget = LineWidget(line, self)
        self.lines_tray.update({line.id_: line_widget})
        with self._no_spacer_and_add_button():
            self.flay.addWidget(line_widget)

    def update_morphemes(self, dict_id: int,
                         field: str,
                         new_value: Optional[str]):
        morphemes = self.document.update_morphemes(dict_id, field, new_value)
        for morpheme in morphemes:
            self.morphemes_tray[morpheme.id_].reset(morpheme)

    def update(self):
        self.update_signal.signal.emit()
        super().update()
