from .tkutils.tokenize import tokenize
from .transforms import transform, AsCode


def FormatCode(source):

    seq = tokenize(source)
    output = AsCode(transform(seq))

    return output
