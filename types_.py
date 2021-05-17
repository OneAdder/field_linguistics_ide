import json
from dataclasses import asdict, is_dataclass, dataclass
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple, Union


class JSONEncoderWithDataClasses(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


@dataclass
class Morpheme:
    text: str
    gloss: str
    id_: Optional[int] = None
    dict_id: Optional[int] = None
    is_stem: Optional[bool] = None

    def __eq__(self, other: 'Morpheme'):
        eq_text = self.text == other.text
        eq_gloss = self.gloss == other.gloss
        return eq_text and eq_gloss


@dataclass
class Token:
    morphemes: List[Morpheme]
    id_: Optional[int] = None
    dict_id: Optional[int] = None


@dataclass
class Line:
    tokens: List[Token]
    translation: str
    id_: Optional[int] = None

    @classmethod
    def new(cls, document: 'Document') -> 'Line':
        morpheme = Morpheme('', '')
        token = Token([])
        document.add_morpheme_to_token(morpheme, token)
        line = cls([], '')
        document.add_token_to_line(token, line)
        return line


class _Dictionary(dict):
    def __init__(self):
        self._gid = 0
        super().__init__()

    def add(self, item: Union[Morpheme, Token]) -> int:
        for index, entry in self.items():
            if entry == item:
                return entry.dict_id
        new_entry = deepcopy(item)
        new_entry.id_ = None
        new_entry.dict_id = self._gid
        self.update({new_entry.dict_id: new_entry})
        self._gid += 1
        return new_entry.dict_id

    @staticmethod
    def _char_keys_to_integers(dictionary_dict: Dict[str, dict],
                               ) -> Dict[int, dict]:
        return {int(key): value for key, value in dictionary_dict.items()}


class TokensDictionary(_Dictionary):
    pass


class MorphemesDictionary(_Dictionary):
    def edit(self, morpheme_id: int, field: str,
             new_value: Union[str, int, None, bool]):
        morpheme = self.get(morpheme_id)
        if not morpheme:
            raise ValueError('Morpheme with dict_id=={} '
                             'is not in the dictionary'.format(morpheme_id))
        setattr(morpheme, field, new_value)

    def find(self, morpheme: Morpheme) -> Optional[int]:
        for morpheme_id, dict_morpheme in self.items():
            if morpheme == dict_morpheme:
                return morpheme_id
        return

    def save(self, path: Path):
        path.write_text(
            json.dumps(self, ensure_ascii=False,
                       indent=4, cls=JSONEncoderWithDataClasses)
        )

    def load_json(self, dictionary_json: str):
        dictionary_dict: Dict[int, dict] = json.loads(dictionary_json)
        dictionary_dict = self._char_keys_to_integers(dictionary_dict)
        for dict_id, item_dict in dictionary_dict.items():
            self.update({dict_id: Morpheme(**item_dict)})
            self._gid = dict_id
        print()


class Document:
    def __init__(self):
        self._morphemes = {}
        self._morphemes_gid = 0
        self._tokens = {}
        self._tokens_gid = 0
        self._lines = {}
        self._lines_gid = 0
        self.data = []
        self.name = 'Unnamed'

    @property
    def morphemes(self):
        return self._morphemes

    @property
    def tokens(self):
        return self._tokens

    @property
    def lines(self):
        return self._lines

    def add_line(self, line: Line):
        if line.id_ is None:
            line.id_ = self._lines_gid
            self._lines_gid += 1
        else:
            self._lines_gid = line.id_ + 1
        self._lines.update({line.id_: line})
        self.data.append(line)

    def add_token_to_line(self, token: Token, line: Line,
                          position: int = -1):
        if token.id_ is None:
            token.id_ = self._tokens_gid
            self._tokens_gid += 1
        else:
            self._tokens_gid = token.id_ + 1
        self._tokens.update({token.id_: token})
        if position == -1:
            line.tokens.append(token)
        else:
            line.tokens.insert(position, token)

    def add_morpheme_to_token(self, morpheme: Morpheme, token: Token,
                              position: int = -1):
        if morpheme.id_ is None:
            morpheme.id_ = self._morphemes_gid
            self._morphemes_gid += 1
        else:
            self._morphemes_gid = morpheme.id_ + 1
        self._morphemes.update({morpheme.id_: morpheme})
        if position == -1:
            token.morphemes.append(morpheme)
        else:
            token.morphemes.insert(position, morpheme)

    def update_morphemes(self,
                         morpheme_dict_id: int,
                         field: str,
                         new_value: str,
                         ) -> Iterator[Morpheme]:
        for morpheme in self._morphemes.values():
            if not morpheme.dict_id == morpheme_dict_id:
                continue
            setattr(morpheme, field, new_value)
            yield morpheme

    def update_morpheme(self, morpheme_id: int,
                        field: str, new_value: str):
        morpheme = self._morphemes.get(morpheme_id)
        if morpheme is None:
            raise ValueError('Morpheme is not in the document')
        setattr(morpheme, field, new_value)

    def pop_morpheme(self, morpheme_id: int) -> Tuple[int, int, Morpheme]:
        self._morphemes.pop(morpheme_id)
        for line in self.data:
            for token in line.tokens:
                for position, morpheme in enumerate(token.morphemes):
                    if morpheme.id_ == morpheme_id:
                        token.morphemes.pop(position)
                        return token.id_, position, morpheme

    def pop_token(self, token_id: int) -> Tuple[int, int, Token]:
        self._tokens.pop(token_id)
        for line in self.data:
            for position, token in enumerate(line.tokens):
                if token.id_ == token_id:
                    line.tokens.pop(position)
                    return token.id_, position, token

    def pop_line(self, line_id: int) -> Tuple[int, int, Line]:
        self._lines.pop(line_id)
        for position, line in enumerate(self.data):
            if line.id_ == line_id:
                self.data.pop(position)
                return line.id_, position, line

    def update_translation(self, line_id: int, new_value: str):
        line = self._lines.get(line_id)
        if line is None:
            raise ValueError('Line is not in the document')
        setattr(line, 'translation', new_value)

    def save(self, path: Path):
        path.write_text(
            json.dumps(self.data, ensure_ascii=False,
                       indent=4, cls=JSONEncoderWithDataClasses)
        )
