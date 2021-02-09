from typing import Sequence, Union

from lambdex.fmt.core.definitions import TokenInfo

from .AsCode import AsCode
from .Reindent import Reindent
from .DropToken import DropToken
from .InsertNewline import InsertNewline
from .CollectComments import CollectComments
from .SuppressWhitespaces import SuppressWhitespaces
from .AnnotateLeadingWhitespace import AnnotateLeadingWhitespace
from .NormalizeWhitespaceBeforeToken import NormalizeWhitespaceBeforeToken
from .NormalizeWhitespaceBeforeComments import NormalizeWhitespaceBeforeComments


def transform(tokenseq: Sequence[TokenInfo]) -> Sequence[TokenInfo]:
    seq = DropToken(tokenseq)
    seq = AnnotateLeadingWhitespace(seq)
    seq = CollectComments(seq)
    seq = SuppressWhitespaces(seq)
    seq = InsertNewline(seq)
    seq = Reindent(seq)
    seq = NormalizeWhitespaceBeforeComments(seq)
    seq = NormalizeWhitespaceBeforeToken(seq)
    return seq


if __name__ == '__main__':
    import sys
    from .tkutils.tokenize import tokenize

    with open(sys.argv[1], 'rb') as fd:
        tokenseq = tokenize(fd.__next__)

        seq = transform(tokenseq)
        code = AsCode(seq)

        print(code)