from ..definitions import tk, A, TokenInfo, actions
from .._stream_base import _StreamWithLog

SUPPRESS_WHITESPACE_AFTER = frozenset([
    A.DECL,
    A.DECL_LPAR,

    A.BODY_RSQB,
    A.CLS_BODY_RSQB,
    A.CLS_DOT,
    A.CLS_DECL,
    A.STMT_END,
])


class SuppressWhitespaces(_StreamWithLog):
    def _handle_token(self, token):
        if self.last_token.annotation in SUPPRESS_WHITESPACE_AFTER and token.is_WS_NL:
            self.action = actions.Default(dont_store=True)
        return ()
