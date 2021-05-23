from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
from PySide2 import QtWidgets as Qt, QtCore, QtGui
from field_linguistics_ide.types_ import MorphemesDictionary, Morpheme
from field_linguistics_ide.user_interface.widgets.common import ScrollArea


class MorphemeItem(QtGui.QStandardItem):
    TYPE = ''

    def __init__(self, morpheme: Morpheme):
        self.morpheme = morpheme
        super().__init__(getattr(morpheme, self.TYPE))
        self.setDropEnabled(False)


class MorphemeTextItem(MorphemeItem):
    TYPE = 'text'


class MorphemeGlossItem(MorphemeItem):
    TYPE = 'gloss'


class FixedItem(QtGui.QStandardItem):
    def __init__(self, label: str = ''):
        super().__init__(label)
        self.setEditable(False)
        self.setDropEnabled(True)


class RemoveButton(FixedItem):
    def __init__(self, morpheme: Morpheme):
        super().__init__('[X]')
        self.morpheme = morpheme
        self.setDropEnabled(False)


class DictionaryModel(QtGui.QStandardItemModel):
    def __init__(self, dictionary: MorphemesDictionary):
        super().__init__()
        self.dictionary = dictionary
        self.morpheme_text_items: Dict[int, MorphemeItem] = {}
        self.morpheme_gloss_items: Dict[int, MorphemeItem] = {}
        self.setHorizontalHeaderLabels(['Text', 'Gloss', ''])
        self.invisibleRootItem().setDropEnabled(False)
        self.stems = FixedItem('Stems')
        self.affixes = FixedItem('Affixes')
        self.appendRow([self.stems, FixedItem(), FixedItem()])
        self.appendRow([self.affixes, FixedItem(), FixedItem()])
        self.unknown = None
        self.populate()
        self.itemChanged.connect(self.edit_item)
        self.edited_morphemes: Deque[Tuple[str, Morpheme]] = deque()
        self.deleted_morphemes: Deque[Morpheme] = deque()

    def edit_item(self, item: MorphemeItem):
        self.dictionary.edit(item.morpheme.dict_id, item.TYPE, item.text())
        self.edited_morphemes.append((item.TYPE, item.morpheme))

    def remove_item(self, item: MorphemeItem):
        self.dictionary.pop(item.morpheme.dict_id)
        self.deleted_morphemes.append(item.morpheme)

    def _add_morpheme(self, tree: QtGui.QStandardItem, morpheme: Morpheme):
        text_item = MorphemeTextItem(morpheme)
        gloss_item = MorphemeGlossItem(morpheme)
        self.morpheme_text_items.update({morpheme.dict_id: text_item})
        self.morpheme_gloss_items.update({morpheme.dict_id: gloss_item})
        tree.appendRow([
            text_item,
            gloss_item,
            RemoveButton(morpheme),
        ])

    def add_morpheme(self, morpheme: Morpheme, new: bool = False):
        if new:
            morpheme.dict_id = self.dictionary.add(morpheme)
        if morpheme.is_stem is True:
            self._add_morpheme(self.stems, morpheme)
        elif morpheme.is_stem is False:
            self._add_morpheme(self.affixes, morpheme)
        else:
            if self.unknown is None:
                self.unknown = FixedItem('Unknown')
                self.appendRow(self.unknown)
            self._add_morpheme(self.unknown, morpheme)

    def edit_morpheme(self, morpheme: Morpheme):
        self.dictionary.edit(morpheme.dict_id, 'text', morpheme.text)
        self.dictionary.edit(morpheme.dict_id, 'gloss', morpheme.gloss)
        self.morpheme_text_items[morpheme.dict_id].setText(morpheme.text)
        self.morpheme_gloss_items[morpheme.dict_id].setText(morpheme.gloss)

    def edit_or_add(self, morpheme: Morpheme):
        if morpheme.dict_id:
            if morpheme.dict_id in self.dictionary:
                self.edit_morpheme(morpheme)
            return
        morpheme_dict_id = self.dictionary.find(morpheme)
        if morpheme_dict_id:
            morpheme.dict_id = morpheme_dict_id
            self.edit_morpheme(morpheme)
        else:
            self.add_morpheme(morpheme, new=True)

    def populate(self):
        for morpheme in self.dictionary.values():
            self.add_morpheme(morpheme)


class TreeView(Qt.QTreeView):
    def __init__(self, model: DictionaryModel):
        super().__init__()
        self.model = model
        self.setModel(model)
        self.expandAll()
        self.header().setSectionResizeMode(Qt.QHeaderView.ResizeToContents)
        self.setDragDropMode(Qt.QAbstractItemView.InternalMove)
        self.clicked[QtCore.QModelIndex].connect(self.remove_item)
        self._current_row: Optional[List[MorphemeTextItem,
                                         MorphemeGlossItem,
                                         RemoveButton]] = None

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        super().dragEnterEvent(event)
        item_index = self.indexAt(event.pos())
        self._current_row = self.take_item(item_index)

    def dropEvent(self, event: QtGui.QDropEvent):
        item_index = self.indexAt(event.pos())
        item = self.model.itemFromIndex(item_index)
        morpheme_item = self._current_row[0]
        if isinstance(item, MorphemeItem):
            parent_index = item_index.parent()
            parent = self.model.itemFromIndex(parent_index)
            parent.appendRow(self._current_row)
            self.model.dictionary.edit(
                morpheme_item.morpheme.dict_id, 'is_stem', item.morpheme.is_stem)
        elif isinstance(item, FixedItem):
            item.appendRow(self._current_row)
            if item.text() == 'Stems':
                self.model.dictionary.edit(
                    morpheme_item.morpheme.dict_id, 'is_stem', True)
            elif item.text() == 'Affixes':
                self.model.dictionary.edit(
                    morpheme_item.morpheme.dict_id, 'is_stem', True)
            else:
                self.model.dictionary.edit(
                    morpheme_item.morpheme.dict_id, 'is_stem', None)
        else:
            raise TypeError('{} instead of MorphemeItem '
                            'or FixedItem'.format(type(item)))
        self._current_row = None

    def _pop_item(self,
                  item: QtGui.QStandardItem,
                  index: QtCore.QModelIndex):
        row = index.row()
        if item.morpheme.is_stem is True:
            return self.model.stems.takeRow(row)
        elif item.morpheme.is_stem is False:
            return self.model.affixes.takeRow(row)
        else:
            return self.model.unknown.takeRow(row)

    def take_item(self, index: QtCore.QModelIndex):
        item = self.model.itemFromIndex(index)
        return self._pop_item(item, index)

    def remove_item(self, index: QtCore.QModelIndex):
        item = self.model.itemFromIndex(index)
        if not isinstance(item, RemoveButton):
            return
        self.model.remove_item(item)
        reply = Qt.QMessageBox.question(
            self, 'Delete entry', 'Delete?',
            Qt.QMessageBox.Yes | Qt.QMessageBox.No,
            Qt.QMessageBox.No,
        )
        if reply == Qt.QMessageBox.No:
            return
        self._pop_item(item, index)


class DictionaryArea(ScrollArea):
    _self = None

    def __init__(self, dictionary: MorphemesDictionary):
        if self._self is not None:
            raise TypeError('{} is already initialized'.format(type(self).__name__))
        super().__init__()
        self.setSizePolicy(Qt.QSizePolicy(Qt.QSizePolicy.Minimum,
                                          Qt.QSizePolicy.Expanding))
        # Qt.QShortcut(QtGui.QKeySequence("Ctrl+z"), self, self.ctrl_z_action)
        self.model = DictionaryModel(dictionary)
        __class__._self = self
        self.tree_view = TreeView(self.model)

    @classmethod
    def get_instance(cls) -> 'DictionaryArea':
        if cls._self is None:
            raise TypeError('{} is not initialized'.format(cls.__name__))
        return cls._self

    def display(self):
        # tree_view = Qt.QTreeView()
        # tree_view.setModel(self.model)
        # tree_view.expandAll()
        # tree_view.header().setSectionResizeMode(Qt.QHeaderView.ResizeToContents)
        # tree_view.clicked[QtCore.QModelIndex].connect(lambda: None)
        # tree_view.setDragDropMode(Qt.QAbstractItemView.InternalMove)
        # # tree_view.dragEnterEvent = self.drag_event
        # super_event = tree_view.dropEvent
        # def drop_event(event: QtGui.QDropEvent):
        #     # print(self.model.itemFromIndex(tree_view.indexAt(event.pos())))
        #     # print(event.dropAction())
        #     # print(event.proposedAction())
        #     item_index = tree_view.indexAt(event.pos())
        #     parent_index = item_index.parent()
        #     parent = self.model.itemFromIndex(parent_index)
        #     row = parent.takeRow(item_index.row())
        #     self._cu = row
        # tree_view.dropEvent = drop_event
        # def drag_event(event: QtGui.QDragEnterEvent):
        #     item_index = tree_view.indexAt(event.pos())
        #     row = self.
        # tree_view.dragEnterEvent = drag_event
        # # tree_view.header().setStretchLastSection(True)
        self.flay.addWidget(self.tree_view)


    def ctrl_z_action(self):
        while self.model.deleted_morphemes:
            morpheme = self.model.deleted_morphemes.pop()
            self.model.add_morpheme(morpheme)
