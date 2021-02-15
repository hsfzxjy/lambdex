from typing import Optional, Tuple, FrozenSet

import re

from lambdex.fmt.utils.colored import colored, colorful

from . import token as tk
from .annotation import Annotation as A


class TokenInfo:

    __slots__ = ['type', 'string', 'start', 'end', 'line', 'annotation', 'leading_whitespace']

    def __init__(
        self,
        type: int,
        string: str,
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
        line: Optional[str] = None,
        annotation: Optional[A] = None,
        leading_whitespace: Optional[str] = None,
    ):
        self.type = type
        self.string = string
        self.start = start
        self.end = end
        self.line = line
        self.annotation = annotation
        self.leading_whitespace = leading_whitespace

    def visualize(self, *, repr=False) -> Optional[str]:
        def _(string):
            return string.__repr__()[1:-1] if repr else string

        if self.start is None or self.end is None or self.line is None:
            return None

        string = self.line
        if not colorful:
            return _(string)

        start, end = self.start[1], self.end[1]

        before = colored(_(string[:start]), 'yellow', attrs=['underline', 'dark'])
        after = colored(_(string[end:]), 'yellow', attrs=['underline', 'dark'])

        middle = self.string
        if not middle:
            middle = '\u2591'
            suffix = ''
        else:
            middle = _(middle)
            suffix = ' '

        middle = colored(middle, 'yellow', attrs=['underline', 'bold'])
        return before + middle + after + suffix

    def __repr__(self) -> str:
        annotated_type = '%d (%s)' % (self.type, tk.tok_name[self.type])
        visualized = self.visualize(repr=True)

        if visualized is None:
            return 'TokenInfo({}, type={:>17s}, A={:>20s}, LWS={})'.format(
                repr(self.string),
                annotated_type,
                repr(self.annotation),
                repr(self.leading_whitespace),
            )
        else:
            return 'TokenInfo({}, type={:>17s}, A={:>20s}, LWS={}, lineno={}:{})'.format(
                visualized,
                annotated_type,
                repr(self.annotation),
                repr(self.leading_whitespace),
                self.start[0],
                self.end[0],
            )

    @property
    def exact_type(self):
        if self.type == tk.OP and self.string in tk.EXACT_TOKEN_TYPES:
            return tk.EXACT_TOKEN_TYPES[self.string]
        else:
            return self.type

    @classmethod
    def new_sentinel_after(cls, token, annotation):
        return cls(
            type=tk.SENTINEL,
            start=token.end,
            end=token.end,
            string='',
            line=token.line,
            annotation=annotation,
        )

    @classmethod
    def new_sentinel_before(cls, token, annotation):
        return cls(
            type=tk.SENTINEL,
            start=token.start,
            end=token.start,
            string='',
            line=token.line,
            annotation=annotation,
        )

    def lxfmt_directive(self) -> Optional[str]:
        if not self.is_CMT:
            return None
        matched = re.match(r'#.*\blxfmt:\s*(?P<directive>on|off)', self.string)
        if matched is not None:
            return matched.group('directive')
        return None

    def __eq__(self, rhs):
        if isinstance(rhs, A):
            return self.annotation == rhs
        return super().__eq__(rhs)

    WS = frozenset([tk.WHITESPACE])
    NL = frozenset([tk.NL, tk.NEWLINE])
    CMT = frozenset([tk.COMMENT, tk.TYPE_IGNORE, tk.TYPE_COMMENT])

    WS_NL = WS | NL
    NL_CMT = NL | CMT
    WS_NL_CMT = WS_NL | CMT

    def _build_property(types: FrozenSet):
        return property(lambda self: self.type in types)

    for name, value in list(locals().items()):
        if not isinstance(value, frozenset):
            continue
        locals()['is_{}'.format(name)] = _build_property(value)
        del locals()[name]

    del name, value


TokenInfo.fake = TokenInfo(type=-1, string=None, annotation=object())