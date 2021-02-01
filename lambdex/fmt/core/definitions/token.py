from ..tkutils.builtins import token as bltk

__all__ = bltk.__all__ + ['ISMATCHED', 'EXACT_TOKEN_TYPES', 'WHITESPACE', 'SENTINEL']


def ISMATCHED(l, r):
    return (l.string, r.string) in {
        ('(', ')'),
        ('[', ']'),
        ('{', '}'),
    }


class auto():
    _counter = bltk.NT_OFFSET

    def __new__(cls):
        cls._counter += 1
        return cls._counter


SENTINEL = auto()
WHITESPACE = auto()

bltk.tok_name.update({
    value: name
    for name, value in globals().items()
    if isinstance(value, int) and not name.startswith('_')
})

from ..tkutils.builtins.token import *
from ..tkutils.builtins.token import EXACT_TOKEN_TYPES

del auto, bltk