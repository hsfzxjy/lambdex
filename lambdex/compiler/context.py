import enum
import random
from functools import partial

__all__ = ['Context', 'ContextFlag']


def random_hex(nbits=32) -> str:
    """
    Return a random number with `nbits` bits in hex string format.
    """
    return hex(random.randint(0, 1 << nbits))[2:].zfill(nbits // 4)


class ContextFlag(enum.Enum):
    # Expect an `ast.stmt`
    should_be_stmt = enum.auto()

    # Expect an `ast.expr`
    should_be_expr = enum.auto()

    # Indicate that this should be the outermost lambdex
    outermost_lambdex = enum.auto()


class Frame:
    __slots__ = ['detached_functions']

    def __init__(self):
        self.detached_functions = []


class Context:
    """
    A `Context` object is passed among rules for sharing global informations.

    Attributes:
    - `compile`: a shorthand for `compile_node(..., ctx)`
    - `globals`: a dict containing globalvars of currently compiling lambdex
    - `used_names`: a set containing currently occupied names
    - `frames`: current `Frame` stack
    """
    __slots__ = ['compile', 'globals', 'used_names', 'frames']

    def __init__(self, compile_fn, globals_dict):
        self.compile = partial(compile_fn, ctx=self)
        self.globals = globals_dict
        self.used_names = set(globals_dict)
        self.frames = []

    def select_name(self, prefix):
        """
        Return a name with prefix `prefix` that is not contained in
        `self.used_names`.
        """
        while True:
            name = '{}_{}'.format(prefix, random_hex())
            if name not in self.used_names:
                return name

    def select_name_and_use(self, prefix):
        """
        Return a name with prefix `prefix` that is not contained in
        `self.used_names`.  The name will be add to `self.used_names`
        before returned.
        """
        name = self.select_name(prefix)
        self.used_names.add(name)
        return name

    def push_frame(self):
        """
        Push a new `Frame` instance to the stack.
        """
        self.frames.append(Frame())
        return self.frames[-1]

    def pop_frame(self):
        """
        Pop the top `Frame` instance from the stack.
        """
        self.frames.pop()

    @property
    def frame(self):
        """
        The top-most `Frame` instance on the stack.
        """
        return self.frames[-1]
