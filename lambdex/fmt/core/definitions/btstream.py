from typing import List, Sequence, Optional

from collections import deque

from lambdex.fmt.utils.logger import getLogger

from .token_info import TokenInfo

logger = getLogger(__name__)


class BufferFrame:
    __slots__ = ['is_backtracing', 'buffer']

    def __init__(self):
        self.is_backtracing = False
        self.buffer = deque()


class BTStream:
    def __init__(self, tokenseq: Sequence[TokenInfo]):
        self.stack = []
        self._backtrace_invoked = False
        self.tokenseq = iter(tokenseq)

    def start_buffer(self):
        assert not self.stack or self.stack[-1].is_backtracing
        logger.debug('== Start Buffer ==')
        self.stack.append(BufferFrame())

    def stop_buffer(self):
        assert self.last_is_buffering(), self.stack
        yield from self.stack[-1].buffer
        if logger.is_debug:
            logger.debug('== Stop Buffer ==')
            for token in self.stack[-1].buffer:
                logger.debug(repr(token))
        self.stack.pop()

    def backtrace(self):
        self.stack[-1].is_backtracing = True
        self._backtrace_invoked = True

        if logger.is_debug:
            logger.debug('')
            logger.debug('Backtracing!')
            for token in self.stack[-1].buffer:
                logger.debug('{}'.format(token))
            logger.debug('')

    def last_is_buffering(self) -> bool:
        return self.stack and not self.stack[-1].is_backtracing

    def _last_bt_frame(self) -> BufferFrame:
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx].is_backtracing:
                return self.stack[idx]

        return None

    def _get_next_token(self) -> Optional[TokenInfo]:
        frame = self._last_bt_frame()
        if frame is None:
            try:
                token = next(self.tokenseq)
            except StopIteration:
                return None
        elif frame.buffer:
            token = frame.buffer.popleft()

        if frame is not None and not frame.buffer:
            if frame is not self.stack[-1]:
                logger.debug('ERROR: frame is not at the last')
                for idx, frame in enumerate(self.stack):
                    logger.debug('== Frame {}: backtracing: {}'.format(idx, frame.is_backtracing))
                    for token in frame.buffer:
                        logger.debug(repr(token))
                    logger.debug('== End of Frame {}'.format(idx))
                raise RuntimeError

            self.stack.remove(frame)

        return token

    def __iter__(self):

        while True:

            token = self._get_next_token()
            if token is None:
                break

            yield token

            if self.last_is_buffering() or self._backtrace_invoked:
                self.stack[-1].buffer.append(token)
                self._backtrace_invoked = False
