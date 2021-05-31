import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional
from collections import deque
from PySide2 import QtGui, QtWidgets as Qt
from field_linguistics_ide.user_interface.templates.main_window import Ui_MainWindow
from field_linguistics_ide.user_interface.widgets import DictionaryArea, DocumentArea
from field_linguistics_ide.loaders.json_loader import JsonLoader
from field_linguistics_ide.loaders.csv_loader import CSVLoader
from field_linguistics_ide.types_ import Document, Morpheme, MorphemesDictionary, Token, Line
from field_linguistics_ide.user_interface.load_dialog import ProjectDialog
from field_linguistics_ide.user_interface.widgets.main_area import MainArea


class UpdateButton(Qt.QPushButton):
    def __init__(self, document_areas):
        super().__init__()
        self._document_areas = document_areas
        self._dictionary_area = DictionaryArea.get_instance()
        self.pressed.connect(self.update)

    def add_document_area(self, document_area: DocumentArea):
        self._document_areas.append(document_area)

    def update(self):
        for document_area in self._document_areas:
            document_area.update()
        super().update()


class App(Qt.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.actionFrom_JSON.triggered.connect(self.load_json)
        self.actionFrom_CSV.triggered.connect(self.load_csv)
        self.project_dir: Optional[Path] = None
        self._document_areas: List[DocumentArea] = []
        self.dictionary_area = DictionaryArea(MorphemesDictionary())
        self.dictionary_area.display()
        self.horizontalLayout.addWidget(self.dictionary_area)
        self.tab_area = MainArea()
        self.tab_area.tab_closed.signal.connect(self.save_all)
        self.exec_project_dialog()
        self.update_button = UpdateButton(self._document_areas)
        self.setWindowTitle('Field Linguistics - {}'.format(self.project_dir.name))
        self.horizontalLayout.addWidget(self.tab_area)
        self.horizontalLayout.addWidget(self.update_button)
        Qt.QShortcut(QtGui.QKeySequence("Ctrl+s"), self, self.save_all)
        self.doc_dir = self.project_dir / 'documents'

    def add_document_area(self, document_area: DocumentArea):
        self._document_areas.append(document_area)
        document_area.update_signal.signal.connect(self.update)
        self.tab_area.addTab(document_area, document_area.document.name)

    def exec_project_dialog(self):
        dialog_window = ProjectDialog()
        dialog_window.create_signal.signal.connect(self.create_project)
        dialog_window.load_signal.signal.connect(self.load_project)
        dialog_window.exec_()

    def _create_project_directory(self):
        while True:
            directory = Qt.QFileDialog.getExistingDirectory(
                self, 'Choose project location', str(Path.home())
            )
            directory = Path(directory) if directory else Path.home()
            if directory.exists() and directory.is_dir():
                self.project_dir = directory / 'Unnamed project'
                if directory.exists():
                    self.load_project(self.project_dir)
                    return
                else:
                    break
        self.project_dir.mkdir()

    def create_project(self):
        self._create_project_directory()
        document = Document()
        document.name = 'Unnamed'
        document_area = DocumentArea(document)
        document_area.display()
        self.add_document_area(document_area)

    def _load_dictionary(self, path: Path):
        self.dictionary_area.model.dictionary.load_json(path.read_text())
        self.dictionary_area.model.populate()

    @staticmethod
    def _load_document(path: Path) -> Document:
        document = Document()
        document_json = json.loads(path.read_text())
        for line_dict in document_json:
            tokens_dicts = line_dict.pop('tokens')
            line = Line([], **line_dict)
            for token_dict in tokens_dicts:
                morpheme_dicts = token_dict.pop('morphemes')
                token = Token([], **token_dict)
                for morpheme_dict in morpheme_dicts:
                    document.add_morpheme_to_token(
                        Morpheme(**morpheme_dict), token)
                document.add_token_to_line(token, line)
            document.add_line(line)
        document.name = path.name[:-5]
        return document

    @staticmethod
    def _load_documents(path: Path) -> Iterable[Document]:
        for doc_path in path.iterdir():
            yield App._load_document(doc_path)

    def load_project(self, path: str):
        self.project_dir = Path(path)
        documents = None
        for filename in self.project_dir.iterdir():
            if filename.name == 'dictionary.json':
                self._load_dictionary(filename)
            if filename.name == 'documents':
                documents = self._load_documents(filename)
        if documents is None:
            raise ValueError('No documents directory found')
        for document in documents:
            document_area = DocumentArea(document)
            document_area.display()
            self.add_document_area(document_area)

    def load_json(self):
        file_name = Qt.QFileDialog.getOpenFileName(
            self, 'Import', str(Path.home()))
        try:
            path = Path(file_name[0])
            loader = JsonLoader(path)
            self.display_document(loader.document)
            for item in loader.morphemes_dictionary.values():
                self.dictionary_area.model.add_morpheme(item, new=True)
        except FileNotFoundError:
            pass

    def load_csv(self):
        file_name = Qt.QFileDialog.getOpenFileName(
            self, 'Import', str(Path.home()))
        try:
            path = Path(file_name[0])
            loader = CSVLoader(path, self.dictionary_area.model)
            loader.load()
            self.display_document(loader.document)
        except FileNotFoundError:
            pass

    def display_document(self, document: Document):
        # draw in scroll area
        document_area = DocumentArea(document)
        document_area.display()
        self.add_document_area(document_area)

    def display_dictionary(self):
        self.dictionary_area.display()
        self.horizontalLayout.addWidget(self.dictionary_area)

    def update(self):
        if self.dictionary_area.model.edited_morphemes:
            while self.dictionary_area.model.edited_morphemes:
                edited_field, edited_entry = \
                    self.dictionary_area.model.edited_morphemes.pop()
                for document_area in self._document_areas:
                    document_area.update_morphemes(
                        edited_entry.dict_id,
                        edited_field,
                        getattr(edited_entry, edited_field),
                    )
        if self.dictionary_area.model.deleted_morphemes:
            while self.dictionary_area.model.deleted_morphemes:
                deleted_morpheme = self.dictionary_area.model.deleted_morphemes.pop()
                for document_area in self._document_areas:
                    deque(document_area.document.update_morphemes(
                        deleted_morpheme.dict_id,
                        'gloss',
                        '',
                    ), maxlen=0)
                    document_area.update_morphemes(deleted_morpheme.dict_id,
                                                   'dict_id', None)
        self.save_all()
        super().update()

    def save_dictionary(self):
        self.dictionary_area.model.dictionary.save(
            self.project_dir / 'dictionary.json'
        )

    def save_document_area(self, document_area: DocumentArea):
        self.doc_dir.mkdir(exist_ok=True)
        document_area.document.save(
            self.doc_dir / '{}.json'.format(document_area.document.name)
        )

    def save_all(self):
        self.save_dictionary()
        for document_area in self._document_areas:
            self.save_document_area(document_area)

    def closeEvent(self, event):
        self.save_all()
        super().closeEvent(event)


def main():
    app = Qt.QApplication(sys.argv)
    window = App()
    window.showMaximized()
    app.exec_()


if __name__ == '__main__':
    main()
