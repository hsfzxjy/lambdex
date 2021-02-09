from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions
from lambdex.fmt.core._stream_base import _StreamWithLog

INSERT_BETWEEN = frozenset({
    (A.BODY_LSQB, A.STMT_START),
    (A.BODY_LSQB, A.BODY_RSQB),
    (A.STMT_COMMA, A.STMT_START),
    (A.LAST_STMT_WITH_COMMA, A.BODY_RSQB),
    (A.LAST_STMT_WITHOUT_COMMA, A.BODY_RSQB),
    #
    (A.CLS_BODY_LSQB, A.STMT_START),
    (A.CLS_BODY_LSQB, A.CLS_BODY_RSQB),
    (A.STMT_COMMA, A.STMT_START),
    (A.LAST_STMT_WITH_COMMA, A.CLS_BODY_RSQB),
    (A.LAST_STMT_WITHOUT_COMMA, A.CLS_BODY_RSQB),
})

START_TOKENS = frozenset(x[0] for x in INSERT_BETWEEN)


class InsertNewline(_StreamWithLog):
    def _init(self):
        self.last_has_newline = False
        self.last_NL = None

    def _ensure_NL_exists_in_buffer(self):
        if not self.last_has_newline:
            self.last_NL = TokenInfo(tk.NL, '\n')
            self.buffer.append(self.last_NL)

    def _annotate_NL_before_RSQB(self, token):
        if token.annotation in {A.BODY_RSQB, A.CLS_BODY_RSQB}:
            self.last_NL.annotation = A.LAST_NL_BEFORE_RSQB

    def _memorize_NL(self, token):
        if token.is_NL:
            self.last_has_newline = True
            self.last_NL = token

    def _reset(self):
        self.last_has_newline = False

    def _handle_token(self, token):
        if token.annotation is None:
            self._memorize_NL(token)
            return ()

        if token.annotation in START_TOKENS:
            if self.buffering:
                self.action = actions.StopBuffer(dont_consume=True)
                return ()
            self.action = actions.StartBuffer()
            return ()

        if (self.last_token.annotation, token.annotation) in INSERT_BETWEEN:
            self._ensure_NL_exists_in_buffer()
            self._annotate_NL_before_RSQB(token)

            self._reset()
            self.action = actions.StopBuffer()
            return ()

        self._reset()
        return ()