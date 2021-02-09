from lambdex.fmt.utils.logger import getLogger

from lambdex.fmt.core._stream_base import _StreamWithLog
from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions

logger = getLogger(__name__)


class NormalizeWhitespaceBeforeComments(_StreamWithLog):
    def _init(self):
        self.newlined = False
        self.leading = False
        self.scope_stack = []

    def _handle_token(self, token: TokenInfo):
        if token.annotation == A.DECL_LPAR:
            self.scope_stack.append(token)
        elif token.annotation == A.DECL_RPAR:
            self.scope_stack.pop()
        elif not self.scope_stack:
            return

        if token.is_NL:
            self.newlined = True
            return

        if token.is_WS:
            if self.newlined:
                self.leading = True

            if not self.buffering:
                self.action = actions.StartBuffer()
            self.newlined = False

            return

        if not token.is_CMT:
            if self.buffering:
                self.action = actions.StopBuffer()
            self.leading = False
            self.newlined = False

            return

        if not self.buffering and not self.newlined:
            yield TokenInfo(tk.WHITESPACE, '  ')
            yield token
            self.action = actions.Default(dont_store=True)
            return

        if self.buffering:
            if any('\\' in x.string for x in self.buffer) or self.leading:
                self.action = actions.StopBuffer()
            else:
                yield TokenInfo(tk.WHITESPACE, '  ')
                yield token
                self.action = actions.StopBuffer(dont_store=True, dont_yield_buffer=True)

            self.leading = False
            self.newlined = False
            return
        self.newlined = False
