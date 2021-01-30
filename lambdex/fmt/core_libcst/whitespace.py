import libcst
import enum
import dataclasses

from typing import Optional

NEWLINE = libcst.Newline()
EMPTY = libcst.SimpleWhitespace('')
EMPTY_LPAR = libcst.LeftParen(EMPTY)
EMPTY_RPAR = libcst.RightParen(EMPTY)
EMPTY_LBRACKET = libcst.LeftSquareBracket(EMPTY)
EMPTY_RBRACKET = libcst.RightSquareBracket(EMPTY)


@dataclasses.dataclass
class State:
    level: int = 0
    default_indent: Optional[str] = None
    is_last_item: bool = False

    def copy(self):
        return dataclasses.replace(self)

    def indentation(self):
        return libcst.SimpleWhitespace(self.default_indent * self.level)

    def last_indentation(self):
        level = self.level
        if self.is_last_item:
            level -= 1
        return libcst.SimpleWhitespace(self.default_indent * level)

    def last_item(self, value=True):
        ret = self.copy()
        ret.is_last_item = value
        return ret

    def incr(self):
        ret = self.copy()
        ret.level += 1
        return ret

    def decr(self):
        ret = self.copy()
        ret.level -= 1
        return ret

    def iincr(self):
        self.level += 1
        return self

    def idecr(self):
        self.level -= 1
        return self

    def new_slot(self):
        return Slot().state(self.copy())


class CommentCollector(libcst.CSTVisitor):
    def __init__(self):
        self._comments = []
        self.trailing_comment = None

    def visit_TrailingWhitespace(self, node: libcst.TrailingWhitespace):
        if self.trailing_comment is None:
            self.trailing_comment = node.comment
            return False

    def visit_Comment(self, node: libcst.Comment):
        self._comments.append(node)

    def comments(self):
        return (x for x in self._comments if x is not None)

    def all_comments(self):
        if self.trailing_comment is not None:
            yield self.trailing_comment

        yield from self.comments()

    def process(self, node):
        if node is libcst.MaybeSentinel.DEFAULT or node is None:
            return self

        node.visit(self)
        return self


class Slot:
    __slots__ = ['_comments', '_state', '_trailing_comment']

    def __init__(self):
        self._comments = []
        self._trailing_comment = None
        self._state: Optional[State] = None

    def merge(self, node: libcst.CSTNode):
        collector = CommentCollector().process(node)
        self._comments.extend(collector.all_comments())
        return self

    def into(self, node: libcst.CSTNode):
        assert self._trailing_comment is None
        collector = CommentCollector().process(node)
        self._comments.extend(collector.comments())
        self._trailing_comment = collector.trailing_comment
        return self

    def state(self, state: State):
        assert self._state is None
        self._state = state
        return self

    def as_node(self):
        assert self._state is not None

        if self._trailing_comment is None:
            first_line = libcst.TrailingWhitespace()
        else:
            first_line = libcst.TrailingWhitespace(
                whitespace=libcst.SimpleWhitespace('  '),
                comment =self._trailing_comment
            )

        indentation = self._state.indentation()
        empty_lines = [
            libcst.EmptyLine(indent=True, whitespace=indentation, comment=comment)
            for comment in self._comments
        ]

        return libcst.ParenthesizedWhitespace(
            first_line=first_line,
            empty_lines=empty_lines,
            indent=True,
            last_line=self._state.last_indentation(),
        )

    def as_lbracket(self):
        return libcst.LeftSquareBracket(self.as_node())

    def as_rbracket(self):
        return libcst.RightSquareBracket(self.as_node())

    def as_lpar(self):
        return libcst.LeftParen(self.as_node())

    def as_rpar(self):
        return libcst.RightParen(self.as_node())

    def as_comma(self):
        return libcst.Comma(whitespace_after=self.as_node())