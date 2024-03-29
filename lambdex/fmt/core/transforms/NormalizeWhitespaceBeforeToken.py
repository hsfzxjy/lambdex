from lambdex.fmt.utils.logger import getLogger

from lambdex.fmt.core._stream_base import _StreamWithLog
from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions

logger = getLogger(__name__)

NORMALIZE_WHITESPACE_BEFORE = {
    A.BODY_LSQB: " ",
    A.CLS_HEAD_LSQB: "",
    A.CLS_BODY_LSQB: " ",
}


class NormalizeWhitespaceBeforeToken(_StreamWithLog):
    def _init(self):
        self.scope_stack = []
        self.prev_non_ws_token = None

    def _handle_token(self, token: TokenInfo):
        if token.annotation == A.DECL_LPAR:
            self.scope_stack.append(token)
        elif token.annotation == A.DECL_RPAR:
            self.scope_stack.pop()
        elif not self.scope_stack:
            return

        if token.is_WS_NL:
            if not self.buffering:
                self.action = actions.StartBuffer()
            return

        if token.annotation in NORMALIZE_WHITESPACE_BEFORE:
            replacement = NORMALIZE_WHITESPACE_BEFORE[token.annotation]
            if (
                self.prev_non_ws_token.annotation != A.CLS_HEAD_RSQB
                and token.annotation == A.CLS_BODY_LSQB
            ):
                replacement = ""
            whitespace = TokenInfo(
                type=tk.WHITESPACE,
                string=replacement,
            )
            yield whitespace

            if self.buffering:
                self.action = actions.StopBuffer(dont_yield_buffer=True)
        elif self.buffering:
            self.action = actions.StopBuffer()

        self.prev_non_ws_token = token