from PySide2 import QtCore, QtGui, QtWidgets as Qt
from field_linguistics_ide.types_ import Morpheme
from field_linguistics_ide.user_interface.signals import BoolSignal, IntSignal
from field_linguistics_ide.user_interface.widgets.document_area.common import EditableLabel, EditableWidgetsArea
from field_linguistics_ide.user_interface.widgets.dictionary_area import DictionaryArea


class DictionaryActions(Qt.QWidget):
    def __init__(self, morpheme: Morpheme):
        self.morpheme = morpheme
        self._start_text = self.morpheme.text
        self._start_gloss = self.morpheme.gloss
        self.dictionary = DictionaryArea.get_instance()
        self.dictionary_entry = \
            self.dictionary.model.dictionary.get(morpheme.dict_id)
        super().__init__()
        self.setHidden(True)
        self.layout_ = Qt.QHBoxLayout()
        self.setLayout(self.layout_)
        self.add = Qt.QPushButton('Add')
        self.edit = Qt.QPushButton('Save')
        self.edit.setEnabled(False)
        self.layout_.addWidget(self.add)
        self.layout_.addWidget(self.edit)
        self.add.pressed.connect(self._add_to_dictionary)
        self.edit.pressed.connect(self._edit_dictionary)
        self.check_in_dict = BoolSignal()
        self.update()

    def update(self):
        if self.morpheme.dict_id is None:
            self.check_in_dict.signal.emit(False)
        else:
            self.check_in_dict.signal.emit(True)
        if self.morpheme.text == self._start_text \
                and self.morpheme.gloss == self._start_gloss:
            self.add.setEnabled(False)
        else:
            self.add.setEnabled(True)
            self.edit.setEnabled(True)
        super().update()

    def _add_to_dictionary(self):
        self.dictionary.model.add_morpheme(self.morpheme, new=True)
        self.update()

    def _edit_dictionary(self):
        self.dictionary.model.edit_or_add(self.morpheme)
        self.update()


class MorphemeTextLabel(EditableLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.editable.contextMenuEvent = self.context_menu_event
        self.split = IntSignal()
        self.split.signal.connect(lambda x: print(x, len(self.editable.text())))

    def context_menu_event(self, menu_event: QtGui.QContextMenuEvent):
        menu: Qt.QMenu = self.editable.createStandardContextMenu()
        action = Qt.QAction('Split')
        action.setText('Split')
        action.triggered.connect(
            lambda *_: self.split.signal.emit(self.editable.cursorPosition()))
        menu.addAction(action)
        menu.exec_(menu_event.globalPos())
        menu.deleteLater()


class MorphemeGlossLabel(EditableLabel):
    def __init__(self, text: str):
        super().__init__(text)

    def highlight_not_in_dict(self, in_dict: bool):
        if in_dict:
            self.fixed.setStyleSheet('')
        else:
            self.fixed.setStyleSheet(
                'border-bottom-width: 1px;'
                'border-bottom-style: solid;'
                'border-radius: 0px;'
                'border-color: brown;'
            )


class MorphemeWidget(EditableWidgetsArea):
    def __init__(self, morpheme: Morpheme, document_area: 'DocumentArea'):
        self.index = None
        self._document_area = document_area
        self.morpheme = morpheme
        self.text_widget = MorphemeTextLabel(morpheme.text)
        self.gloss_widget = MorphemeGlossLabel(morpheme.gloss)
        self.dictionary_actions = DictionaryActions(morpheme)
        self.dictionary_actions.check_in_dict.signal.connect(
            self.gloss_widget.highlight_not_in_dict)
        super().__init__()
        self.layout.addWidget(self.text_widget)
        self.layout.addWidget(self.gloss_widget)
        self.layout.addWidget(self.dictionary_actions)
        self.split = IntSignal()
        self.text_widget.split.signal.connect(self.split.signal.emit)

    def text(self) -> str:
        return self.text_widget.text()

    @classmethod
    def from_deleted(cls, token_id: int, morpheme_position: int,
                     morpheme: Morpheme, document_area: 'DocumentArea') -> 'MorphemeWidget':
        document = document_area.document
        token = document.tokens[token_id]
        document.add_morpheme_to_token(morpheme, token, morpheme_position)
        self = cls(morpheme, document_area)
        return self

    def reset(self, morpheme: Morpheme):
        self.text_widget.setText(morpheme.text)
        self.gloss_widget.setText(morpheme.gloss)

    def _fixed_mode(self):
        self.text_widget.set_editable(False)
        self.gloss_widget.set_editable(False)
        self.dictionary_actions.setHidden(True)

    def _editable_mode(self):
        self.text_widget.set_editable(True)
        self.gloss_widget.set_editable(True)
        self.dictionary_actions.setHidden(False)
        self._document_area.editing_morphemes.append(self)

    def focus_proxy_action(self):
        self.text_widget.focus_to_editable()

    def update_document(self, field: str, widget: Qt.QWidget):
        self._document_area.document.update_morpheme(self.morpheme.id_,
                                                     field, widget.text())

    def update_text(self, text: str):
        self.text_widget.update_fixed(text)
        self.update_document('text', self.text_widget)
        self.dictionary_actions.update()

    def update_gloss(self, text: str):
        self.gloss_widget.update_fixed(text)
        self.update_document('gloss', self.gloss_widget)
        self.dictionary_actions.update()

    def set_morpheme_dict_id_none(self, _):
        self.morpheme.dict_id = None

    def connect_editable_labels(self):
        self.text_widget.editable.textEdited.connect(self.update_text)
        self.gloss_widget.editable.textEdited.connect(self.update_gloss)
        self.text_widget.editable.textEdited.connect(self.set_morpheme_dict_id_none)
        self.gloss_widget.editable.textEdited.connect(self.set_morpheme_dict_id_none)

    def delete_action(self):
        data = self._document_area.document.pop_morpheme(self.morpheme.id_)
        self._document_area.deleted_morphemes.append(data)
        self._document_area.morphemes_tray.pop(self.morpheme.id_)
