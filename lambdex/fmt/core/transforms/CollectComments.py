from ...utils.logger import getLogger

from .._stream_base import _StreamWithLog
from ..definitions import tk, A, TokenInfo, actions

logger = getLogger(__name__)

BEFORE = 1
AFTER = 2


def _match_rule(pattern, rules):
    pattern = tuple(pattern)
    for rule in rules:
        if len(pattern) > len(rule.pattern): continue
        if pattern == rule.pattern[:len(pattern)]: return True, rule, len(pattern) == len(rule.pattern)

    return False, None, False


class _CollectRule:
    __slots__ = ['pattern', 'insert_at']

    def __init__(self, *, insert_at: int, pattern: tuple):
        self.pattern = pattern
        self.insert_at = insert_at


COLLECT_BACKWARD = [
    _CollectRule(
        insert_at=AFTER,
        pattern=(A.DECL, A.DECL_LPAR, A.DECL_LAMBDA, A.BODY_LSQB),
    ),
    _CollectRule(
        insert_at=AFTER,
        pattern=(A.CLS_HEAD_RSQB, A.CLS_BODY_LSQB),
    ),
    _CollectRule(
        insert_at=AFTER,
        pattern=(A.STMT_END, A.STMT_COMMA, A.LAST_STMT_WITH_COMMA),
    ),
    _CollectRule(
        insert_at=BEFORE,
        pattern=(A.STMT_END, A.STMT_COMMA, A.STMT_START),
    ),
]

COLLECT_FORWARD = [
    _CollectRule(
        insert_at=BEFORE,
        pattern=(A.BODY_RSQB, A.DECL_RPAR),
    ),
    _CollectRule(
        insert_at=BEFORE,
        pattern=(A.CLS_BODY_RSQB, A.CLS_DOT, A.CLS_DECL, A.CLS_HEAD_LSQB),
    ),
    _CollectRule(
        insert_at=BEFORE,
        pattern=(A.CLS_BODY_RSQB, A.CLS_DOT, A.CLS_DECL, A.CLS_BODY_LSQB),
    ),
]

START_TOKENS = frozenset(x.pattern[0] for x in COLLECT_FORWARD + COLLECT_BACKWARD)


class CollectComments(_StreamWithLog):
    def _split_buffer(self):
        comments, others = [], []
        # for idx,token in self.buffer:

        iterator = iter(self.buffer)

        def _next():
            try:
                return next(iterator)
            except StopIteration:
                return TokenInfo.fake

        while True:
            token = _next()
            if token is TokenInfo.fake:
                break

            if token.is_CMT:
                comments.append(token)
                token = _next()
                assert token.is_NL
                comments.append(token)
            else:
                others.append(token)

        return comments, others

    def _handle_token(self, token):
        if token.annotation is None: return

        if not self.buffering:
            if token.annotation in START_TOKENS:
                self.action = actions.StartBuffer()
                self.pattern = [token.annotation]
            return

        self.pattern.append(token.annotation)

        matched, rule, exhausted = _match_rule(self.pattern, COLLECT_BACKWARD)
        if matched and exhausted:
            comments, others = self._split_buffer()

            yield from others
            if rule.insert_at == BEFORE:
                yield from comments
                yield token
            else:
                yield token
                yield from comments

            self.action = actions.StopBuffer(dont_yield_buffer=True, dont_store=True)
            return
        elif matched:
            return

        matched, rule, exhausted = _match_rule(self.pattern, COLLECT_FORWARD)
        if matched and exhausted:
            comments, others = self._split_buffer()
            assert rule.insert_at == BEFORE

            yield from comments
            yield from others
            yield token

            self.action = actions.StopBuffer(dont_yield_buffer=True, dont_store=True)
            return
        elif matched:
            return

        self.action = actions.StopBuffer(dont_consume=True)
