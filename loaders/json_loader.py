import json
from pathlib import Path
from field_linguistics_ide.types_ import Document, Morpheme, MorphemesDictionary, Line, Token, TokensDictionary


class JsonLoader:
    def __init__(self, path: Path):
        self.json = json.loads(path.read_text())
        self.document = Document()
        self.morphemes_dictionary = MorphemesDictionary()
        self.tokens_dictionary = TokensDictionary()
        self.load()

    def load(self):
        for raw_line in self.json:
            line = Line([], raw_line['translation'])
            glossed_line = raw_line.get('glosses', len(raw_line['text']) * [None])
            for text, glosses in zip(raw_line['text'], glossed_line):
                new_token = Token([])
                text = text.split('-')
                glossed_token = glosses.split('-') if glosses else len(text) * [None]
                for morpheme, gloss in zip(text, glossed_token):
                    new_morpheme = Morpheme(morpheme, gloss)
                    if gloss:
                        new_morpheme.is_stem = not gloss.isupper()
                        new_morpheme.dict_id = self.morphemes_dictionary.add(new_morpheme)
                    self.document.add_morpheme_to_token(new_morpheme, new_token)
                new_token.dict_id = self.tokens_dictionary.add(new_token)
                self.document.add_token_to_line(new_token, line)
            self.document.add_line(line)


# j = JsonLoader(Path('/home/misha/Проекты/дисер/linguistics_planet/vasya.json'))
# j.load()
# print()
