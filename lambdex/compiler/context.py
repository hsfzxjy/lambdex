import enum
import random
from functools import partial

from lambdex.utils import compat
from lambdex.utils.ast import is_lvalue, is_coroutine_ast

from . import error

__all__ = ['Context', 'ContextFlag']


def random_hex(nbits=32) -> str:
    """
    Return a random number with `nbits` bits in hex string format.
    """
    return hex(random.randint(0, 1 << nbits))[2:].zfill(nbits // 4)


auto = compat.enum_auto()


class ContextFlag(enum.Enum):

    # Expect an `ast.stmt`
    should_be_stmt = auto()

    # Expect an `ast.expr`
    should_be_expr = auto()

    # Indicate that this should be the outermost lambdex
    outermost_lambdex = auto()


del auto


class Frame:
    __slots__ = ['detached_functions', 'name', 'is_async']

    def __init__(self):
        self.name = None
        self.is_async = False
        self.detached_functions = []


EM_HEAD_FOUND = "expect only one group of '[]'"
EM_HEAD_MISSING = "expect another group of '[]'"
EM_TOO_MANY_ITEMS = "expect only one item inside '[]'"
EM_UNEXPECTED_CLAUSE = 'unexpected clause'
EM_NOT_LVALUE = 'cannot be assigned'


class Context:
    """
    A `Context` object is passed among rules for sharing global informations.

    Attributes:
    - `compile`: a shorthand for `compile_node(..., self)`
    - `globals`: a dict containing globalvars of currently compiling lambdex
    - `used_names`: a set containing currently occupied names
    - `frames`: current `Frame` stack
    """
    __slots__ = ['compile', 'globals', 'used_names', 'frames', 'filename', 'renames']

    def __init__(self, compile_fn, globals_dict, filename):
        self.compile = partial(compile_fn, ctx=self)
        self.globals = globals_dict
        self.used_names = set(globals_dict)
        self.frames = []
        self.filename = filename
        self.renames = {}

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

    # Below are helper functions for compile-time assertion

    def assert_(self, cond: bool, msg: str, node):
        error.assert_(cond, msg, node, self.filename)

    def raise_(self, msg: str, node):
        error.assert_(False, msg, node, self.filename)

    def assert_is_instance(self, node, type_: type, msg):
        self.assert_(isinstance(node, type_), msg, node)

    def assert_single_head(self, clause):
        self.assert_(clause.single_head(), EM_TOO_MANY_ITEMS, lambda: clause.head[1])

    def assert_single_body(self, clause):
        self.assert_(clause.single_body(), EM_TOO_MANY_ITEMS, lambda: clause.body[1])

    def assert_clause_num_at_most(self, clauses, num: int):
        self.assert_(len(clauses) <= num, EM_UNEXPECTED_CLAUSE, lambda: clauses[num].node)

    def assert_no_head(self, clause):
        self.assert_(clause.no_head(), EM_HEAD_FOUND, lambda: clause.node)

    def assert_head(self, clause):
        self.assert_(clause.head, EM_HEAD_MISSING, lambda: clause.node)

    def assert_name_equals(self, clause, name: str):
        self.assert_(clause.name == name, 'expect {!r}'.format(name), clause.node)

    def assert_name_in(self, clause, names):
        self.assert_(clause.name in names, 'expect ' + ' or '.join(map(repr, names)), clause.node)

    def assert_lvalue(self, node):
        check_result, failed_at = is_lvalue(node)
        self.assert_(check_result, EM_NOT_LVALUE, failed_at)

    def check_coroutine(self, x, node, keyword):
        if is_coroutine_ast(x):
            self.assert_(
                self.frame.is_async,
                '{!r} outside async function'.format(keyword),
                node,
            )
