from typing import Sequence

import abc

from lambdex.fmt.utils.logger import getLogger, IS_DEBUG
from .definitions import TokenInfo, actions


class _StreamBase(abc.ABC):
    def __init__(self, tokenseq: Sequence[TokenInfo]):
        self.buffering = False
        self.last_token = TokenInfo.fake
        self.buffer = []
        self.action = actions.Default()

        self.tokenseq = tokenseq

        self._init()

    def _init(self):
        pass

    def __iter__(self):
        def _stream():
            token = None
            iterator = iter(self.tokenseq)
            while True:
                if not self.action.dont_consume:
                    try:
                        token = next(iterator)
                    except StopIteration:
                        break
                yield token

        for token in _stream():
            self.action = actions.Default()
            yield from self._handle_token(token)
            self.action = actions.BaseAction.from_(self.action)
            yield from self._handle_action(token, self.action)

    @abc.abstractmethod
    def _handle_token(self, token: TokenInfo):
        pass

    def _update_last_token(self, token: TokenInfo):
        if token.annotation is not None:
            self.last_token = token

    def _handle_action(self, token: TokenInfo, action: actions.BaseAction) -> Sequence[TokenInfo]:

        if actions.Default.is_class_of(action):
            yield from self._handle_default(token)
        elif actions.StartBuffer.is_class_of(action):
            yield from self._handle_start_buffer(token)
        elif actions.StopBuffer.is_class_of(action):
            yield from self._handle_stop_buffer(token)
        else:
            yield from self._handle_unknown_action(token, action)

    def _append_buffer(self, token):
        self.buffer.append(token)

    def _handle_default(self, token):
        if self.buffering:
            assert self.action.no_special, self.action
            self._append_buffer(token)
            return

        if self.action.no_special:
            yield token

        self._update_last_token(token)

    def _handle_start_buffer(self, token):
        assert not self.buffering
        self.buffering = True
        self._append_buffer(token)
        self._update_last_token(token)
        return ()

    def _handle_stop_buffer(self, token):
        assert self.buffering
        self.buffering = False
        if not self.action.dont_yield_buffer:
            yield from self.buffer
        if self.action.no_special:
            yield token
        self.buffer.clear()
        self._update_last_token(token)
        return ()

    def _handle_unknown_action(self, token, action):
        return ()


class _StreamWithLog(_StreamBase):
    def __iter__(self):
        logger = getLogger(__name__)
        for token in super().__iter__():
            yield token
            logger.debug(token)


if not IS_DEBUG:
    _StreamWithLog = _StreamBase