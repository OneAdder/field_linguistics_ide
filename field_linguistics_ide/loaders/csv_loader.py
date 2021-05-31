from typing import Iterable
from collections import namedtuple
from pathlib import Path

from field_linguistics_ide.types_ import Document, Line, Morpheme, Token
from field_linguistics_ide.user_interface.widgets.dictionary_area import DictionaryModel

_CsvLine = namedtuple('_CsvLine', ['text', 'glosses', 'translation'])


class CSVLoader:
    def __init__(self, path: Path, morphemes_model: DictionaryModel):
        self.csv = path.read_text()
        self.document: Document = Document()
        self.morphemes_model = morphemes_model

    def _preprocess(self) -> Iterable[_CsvLine]:
        result_line = _CsvLine([], [], [])
        for line in self.csv.split('\n'):
            split_line = line.split()
            if not split_line:
                continue
            if split_line[0] == '\\Text':
                token = [t.split('-')for t in split_line[1:]]
                result_line.text.extend(token)
            elif split_line[0] == '\\Glosses':
                token = [t.split('-') for t in split_line[1:]]
                result_line.glosses.extend(token)
            elif split_line[0] == '\\Translation':
                result_line.translation.extend(split_line[1:])
                yield result_line
                result_line = _CsvLine([], [], [])
            else:
                continue

    def load(self):
        for csv_line in self._preprocess():
            line = Line([], ' '.join(csv_line.translation))
            for text, glosses in zip(csv_line.text, csv_line.glosses):
                new_token = Token([])
                for morpheme, gloss in zip(text, glosses):
                    new_morpheme = Morpheme(morpheme, gloss)
                    if gloss:
                        new_morpheme.is_stem = not gloss.isupper()
                        self.morphemes_model.edit_or_add(new_morpheme)
                    self.document.add_morpheme_to_token(new_morpheme, new_token)
                self.document.add_token_to_line(new_token, line)
            self.document.add_line(line)
