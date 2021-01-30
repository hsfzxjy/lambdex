import libcst
from pathlib import Path

from . import whitespace as ws
from .frame import StackFrame
from .patterns import *


class MainTransformer(libcst.CSTTransformer):
    def __init__(self):
        self._context_stack = [StackFrame.new_unknown(None)]
        self.ws_state = ws.State()

    @property
    def last(self):
        return self._context_stack[-1]

    def push(self, frame):
        if frame.is_body:
            self.ws_state.iincr()
        self._context_stack.append(frame)

    def pop(self):
        frame = self._context_stack.pop()
        if frame.is_body:
            self.ws_state.idecr()
        return frame

    def visit_Module(self, node: libcst.Module):
        self.ws_state.default_indent = node.default_indent

    def visit_Call(self, node: libcst.Call):
        is_lambdex = matches(node, M_LAMBDEX)
        self.push(StackFrame.new_lambdex_if(is_lambdex, node))

    def leave_Call(self, node, updated_node):
        if self.pop().is_lambdex:
            updated_node = updated_node.with_changes(whitespace_before_args=ws.EMPTY)

        return updated_node

    def leave_Arg(self, node, updated_node):
        if self.last.is_lambdex:
            updated_node = updated_node.with_changes(whitespace_after_arg=ws.EMPTY, comma=libcst.MaybeSentinel)

        return updated_node

    def visit_List(self, node):
        self.push(StackFrame.new_body_if(self.last.is_lambdex, node))

    def leave_List(self, node, updated_node: libcst.List):
        if self.pop().is_body:
            pre_slot = self.ws_state \
                .incr().new_slot() \
                .merge(self.last.node.whitespace_before_args) \
                .into(node.lbracket.whitespace_after)

            updated_node = updated_node.with_changes(
                lbracket=pre_slot.as_lbracket(),
                rbracket=ws.EMPTY_RBRACKET,
            )

        return updated_node

    def visit_Element(self, node: libcst.Element):
        self.push(StackFrame.new_stmt_if(self.last.is_body, node))

    def leave_Element(self, node: libcst.Element, updated_node: libcst.Element):
        if not self.pop().is_stmt:
            return updated_node

        is_last_element = node is self.last.node.elements[-1]
        slot = self.ws_state \
            .last_item(is_last_element) \
            .new_slot() \
            .into(node.comma)

        if is_last_element:
            slot \
                .merge(self.last.node.rbracket.whitespace_before) \
                .merge(self._context_stack[-2].node.args[-1].whitespace_after_arg) \
                .merge(self._context_stack[-2].node.args[-1].comma)

        return updated_node.with_changes(comma=slot.as_comma())

    def visit_Subscript(self, node: libcst.Subscript):
        is_header = self.last.is_clause and self.last.node.value is node
        if is_header:
            self.push(StackFrame.new_unknown(node))
            return
        is_clause = matches(node, M_CLAUSE)
        self.push(StackFrame.new_clause_if(is_clause, node))

    def leave_Subscript(self, node: libcst.Subscript, updated_node: libcst.Subscript):
        if self.pop().is_clause:
            slot = self.ws_state \
                .incr() \
                .new_slot() \
                .into(node.lbracket.whitespace_after)
            updated_node = updated_node.with_changes(
                lbracket=slot.as_lbracket(),
                rbracket=ws.EMPTY_RBRACKET,
            )

        return updated_node

    def visit_Subscript_slice(self, node):
        self.push(StackFrame.new_body_if(self.last.is_clause, node))

    def leave_Subscript_slice(self, node):
        self.pop()

    def visit_SubscriptElement(self, node: libcst.SubscriptElement):
        self.push(StackFrame.new_stmt_if(self.last.is_body, node))

    def leave_SubscriptElement(self, node: libcst.SubscriptElement, updated_node: libcst.SubscriptElement):
        if not self.pop().is_stmt:
            return updated_node

        is_last_element = node is self.last.node.slice[-1]
        slot = self.ws_state \
            .last_item(is_last_element) \
            .new_slot() \
            .into(node.comma)

        if is_last_element:
            slot.merge(self.last.node.rbracket)

        return updated_node.with_changes(comma=slot.as_comma())


def handle_file(filename: str):
    content = Path(filename).read_text()
    tree = libcst.parse_module(content)
    transformer = MainTransformer()
    new_tree = tree.visit(transformer)
    Path(filename).write_text(new_tree.code)
