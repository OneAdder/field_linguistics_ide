from collections import namedtuple
from pathlib import Path

Line = namedtuple('Line', ['text', 'glosses', 'translation'])


def load(path: Path):
    text = path.read_text()
    result = []
    line_contents = []
    for line in text.split('\n'):
        split_line = line.split(',')
        if split_line[0] == '\Text':
            pass
