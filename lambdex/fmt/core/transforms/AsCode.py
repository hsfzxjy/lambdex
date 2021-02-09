from typing import Sequence, Union

from lambdex.fmt.core.definitions import TokenInfo, tk


def AsCode(tokenseq: Sequence[TokenInfo], *, encode=False) -> Union[str, bytes]:
    encoding = ''
    token_strings = []
    for token in tokenseq:
        if token.type == tk.ENCODING:
            encoding = token.string
        else:
            token_strings.append(token.string)
    result = ''.join(token_strings)
    if encode:
        result = result.encode(encoding)
    return result
