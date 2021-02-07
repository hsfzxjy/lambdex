from typing import Tuple

from ...utils.logger import getLogger

from .state import State
from .token_info import TokenInfo

logger = getLogger(__name__)


class Context:
    def __init__(self):
        self.ret = []
        self.op_stack = []
        self.state_stack = [State.UNKNOWN]
        self.cache = None

    @property
    def last_op(self) -> TokenInfo:
        return self.op_stack[-1]

    @property
    def last_state(self) -> State:
        return self.state_stack[-1]

    def debug(self, text):
        if not logger.is_debug:
            return

        import sys
        frame = sys._getframe(2)
        logger.debug('====> {}'.format(text))
        logger.debug('==> {} {}'.format(frame.f_code.co_filename, frame.f_lineno))
        logger.debug('==> {}'.format(frame.f_locals['token']))

        logger.debug('{:^60s}'.format('--- OP Stack ---'))
        for op, state in self.op_stack:
            logger.debug('{:>20s}{:>20s}{:>20s}'.format(
                op.string,
                op.annotation.name if op.annotation is not None else '',
                state.name,
            ))
        logger.debug('{:^60s}'.format('--- ST Stack ---'))
        for x in self.state_stack:
            logger.debug('{:>60s}'.format(x.name))

    def error(self):
        self.debug('ERROR')
        raise RuntimeError

    def push_ret(self, v: TokenInfo) -> None:
        self.ret.append(v)

    def push_op(self, v: TokenInfo) -> None:
        self.op_stack.append((v, self.last_state))
        self.debug('PUSH OP AFTER')

    def pop_op(self) -> Tuple[TokenInfo, State]:
        ret = self.op_stack.pop()
        self.debug('POP OP AFTER')
        return ret

    def push_state(self, v: State) -> None:
        self.state_stack.append(v)
        self.debug('PUSH State AFTER')

    def pop_state(self) -> State:
        popped = self.state_stack.pop()
        self.debug('POP State AFTER')
        return popped
