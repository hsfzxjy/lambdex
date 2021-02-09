import functools

from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions
from lambdex.fmt.core._stream_base import _StreamWithLog

ANNOTATIONS_TO_DROP = frozenset([
    A.DECL_ARG_COMMA,
])


class DropToken(_StreamWithLog):
    def _handle_token(self, token: TokenInfo):
        if token.annotation in ANNOTATIONS_TO_DROP:
            self.action = actions.Default(dont_store=True)
        return ()
