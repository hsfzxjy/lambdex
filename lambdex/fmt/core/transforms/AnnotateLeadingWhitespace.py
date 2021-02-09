from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions
from lambdex.fmt.core._stream_base import _StreamWithLog


class AnnotateLeadingWhitespace(_StreamWithLog):
    def _init(self):
        self.newlined = False
        self.last_leading_whitespace = ''

    def _handle_token(self, token: TokenInfo):
        if self.newlined:
            if token.is_WS and self.last_token.annotation in (
                    A.STMT_START,
                    A.CLS_HEAD_LSQB,
            ):
                token.leading_whitespace = self.last_leading_whitespace
            elif token.is_WS:
                self.last_leading_whitespace = token.string
            else:
                self.last_leading_whitespace = ''
            self.newlined = False

        if token.is_NL:
            self.newlined = True

        return ()
