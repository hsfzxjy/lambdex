import enum
import random
from functools import partial

__all__ = ['Context', 'ContextFlag']


def random_hex(nbits=32):
    return hex(random.randint(0, 1 << nbits))[2:].zfill(nbits // 4)


class ContextFlag(enum.Enum):
    should_be_stmt = enum.auto()
    unset = enum.auto()


class Context:
    __slots__ = ['compile', 'globals', 'used_names']

    def __init__(self, compile_fn, globals_dict):
        self.compile = partial(compile_fn, ctx=self)
        self.globals = globals_dict
        self.used_names = set(globals_dict)

    def select_name(self, prefix):
        while True:
            name = '{}_{}'.format(prefix, random_hex())
            if name not in self.used_names:
                return name

    def select_name_and_use(self, prefix):
        name = self.select_name(prefix)
        self.used_names.add(name)
        return name