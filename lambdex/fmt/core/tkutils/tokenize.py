from typing import List

from lambdex.fmt.core._stream_base import _StreamWithLog
from lambdex.fmt.core.definitions import TokenInfo, tk, Context, A, actions, BTStream

from .rules import matcher
from .builtins import tokenize as bltokenize


class AddWhitespace(_StreamWithLog):
    def _handle_token(self, token: TokenInfo):
        ws_start = ws_end = None
        last_token = self.last_token
        if last_token is TokenInfo.fake or last_token.type == tk.ENCODING:
            pass
        elif last_token.is_WS_NL:  # NEWLINE or CONTINUE
            assert token.start[0] == last_token.end[0] + 1
            if token.start[1] != 0:
                ws_start = (token.start[0], 0)
                ws_end = token.start
        elif last_token.end != token.start:
            assert last_token.end[0] == token.start[0]
            ws_start = last_token.end
            ws_end = token.start

        if ws_start is not None:
            whitespace_token = TokenInfo(
                tk.WHITESPACE,
                token.line[ws_start[1]:ws_end[1]],
                ws_start,
                ws_end,
                token.line,
            )
            yield whitespace_token

        self.last_token = token
        yield token

        self.action = actions.Default(dont_store=True)


class RearrangeSentinel(_StreamWithLog):
    def _init(self):
        self.stmt_start_in_buffer = None

    def _handle_token(self, token: TokenInfo):
        if (token.is_WS_NL_CMT or token == A.STMT_START):
            if not self.buffering:
                self.action = actions.StartBuffer()
        elif self.buffering:
            if self.stmt_start_in_buffer is not None:
                yield from self.buffer

                # collapse STMT_START and STMT_END if adjcent
                if token != A.STMT_END:
                    yield self.stmt_start_in_buffer
                    yield token
            elif token == A.STMT_END:
                yield token
                yield from self.buffer
            else:
                yield from self.buffer
                yield token
            self.stmt_start_in_buffer = None
            self.action = actions.StopBuffer(dont_yield_buffer=True, dont_store=True)

    def _append_buffer(self, token):
        if token == A.STMT_START:
            self.stmt_start_in_buffer = token
        else:
            self.buffer.append(token)


class HandleLastSTMT(_StreamWithLog):
    def _init(self):
        self.insert_last_stmt_at = None

    def _append_buffer(self, token):
        self.buffer.append(token)
        if token == A.STMT_COMMA:
            self.insert_last_stmt_at = len(self.buffer)

    def _handle_token(self, token: TokenInfo):
        if token.annotation == A.STMT_END and not self.buffering:
            self.action = actions.StartBuffer()
        elif self.buffering and token.annotation in (
                A.BODY_RSQB,
                A.CLS_BODY_RSQB,
                A.STMT_START,
        ):

            if token.annotation != A.STMT_START:
                pos = self.insert_last_stmt_at
                if pos is None:
                    annotation = A.LAST_STMT_WITHOUT_COMMA
                else:
                    annotation = A.LAST_STMT_WITH_COMMA
                pos = pos or 1

                yield from self.buffer[:pos]
                yield TokenInfo.new_sentinel_after(self.buffer[pos - 1], annotation)
                yield from self.buffer[pos:]
            else:
                yield from self.buffer

            self.insert_last_stmt_at = None
            self.action = actions.StopBuffer(dont_yield_buffer=True)
        elif self.buffering and token == A.STMT_START:
            self.insert_last_stmt_at = None
            self.action = actions.StopBuffer()


class Annotate(_StreamWithLog):
    def _init(self):
        assert isinstance(self.tokenseq, BTStream)

        self.context = Context()
        self.context.is_buffering = lambda: self.tokenseq.last_is_buffering()

    def _handle_token(self, token):
        self.context.tokenseq = self.tokenseq
        self.action = matcher.dispatch(self.context, token)
        return ()

    def _handle_default(self, token):
        if self.action.dont_store:
            assert not self.tokenseq.last_is_buffering()
            yield from self.context.ret
            self.context.ret.clear()
            return

        assert not self.context.ret

        if self.tokenseq.last_is_buffering():
            return

        if self.action.dont_consume:
            return

        yield token

    def _handle_start_buffer(self, token):
        self.tokenseq.start_buffer()
        return ()

    def _handle_stop_buffer(self, token):
        yield from self.tokenseq.stop_buffer()

        if self.action.no_special:
            yield token
        elif self.action.dont_store:
            yield from self.context.ret
            self.context.ret.clear()

    def _handle_unknown_action(self, token, action):

        assert actions.Backtrace.is_class_of(action)
        if action.new_state is not None:
            self.context.state_stack[-1] = action.new_state
        self.tokenseq.backtrace()
        return ()


def tokenize(readline):
    seq = bltokenize.tokenize(readline)
    seq = AddWhitespace(seq)
    seq = BTStream(seq)
    seq = Annotate(seq)
    seq = RearrangeSentinel(seq)
    seq = HandleLastSTMT(seq)

    return seq


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as fd:
        tokenize(fd.__next__)
