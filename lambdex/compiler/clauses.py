import ast
from collections import namedtuple

from lambdex.utils.ast import value_from_subscript


class Clause(namedtuple('_Clause', 'name head body')):
    def no_head(self):
        return self.head is None

    def no_body(self):
        return len(self.body) == 0

    def single_body(self):
        return len(self.body) == 1

    def try_tuple_body(self, ctx=ast.Load()):
        if self.single_body():
            return self.body[0]

        return ast.Tuple(elts=self.body, ctx=ctx)

    def unwrap_body(self):
        assert self.single_body()
        return self.body[0]

    def single_head(self):
        return self.head is not None and len(self.head) == 1

    def unwrap_head(self):
        assert self.single_head()
        return self.head[0]


class Clauses(list):
    def single(self):
        return len(self) == 1


def match_clauses(node):

    results = []
    body = head = name = None
    while node is not None:
        if isinstance(node, ast.Subscript) and body is None:
            body = value_from_subscript(node, force_list=True)
            node = node.value
            continue

        if isinstance(node, ast.Call) and head is None:
            head = node.args
            node = node.func
            continue

        if isinstance(node, ast.Attribute) and name is None:
            name = node.attr
            next_node = node.value

        if isinstance(node, ast.Name) and name is None:
            name = node.id
            next_node = None

        if name is not None:
            results.append(Clause(name, head, body))
            body = head = name = None
            node = next_node
            continue

        return

    return Clauses(results[::-1])