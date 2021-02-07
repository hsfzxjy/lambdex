import ast
from collections import namedtuple

from lambdex.utils.ast import value_from_subscript


class Clause(namedtuple('_Clause', 'node name head body')):
    def no_head(self) -> bool:
        """
        Check that whether the head is None.
        """
        return self.head is None

    def single_body(self) -> bool:
        """
        Check that whether the body has only one item.
        """
        return len(self.body) == 1

    def try_tuple_body(self, ctx=ast.Load()):
        """
        If body has single item, return it.  Otherwise, wrap the items in
        an `ast.Tuple` and return.
        """
        if self.single_body():
            return self.body[0]

        return ast.Tuple(elts=self.body, ctx=ctx)

    def unwrap_body(self):
        """
        Check that the body has only one item, and return it.
        """
        assert self.single_body()
        return self.body[0]

    def single_head(self) -> bool:
        """
        Check whether the head has only one item.
        """
        return self.head is not None and len(self.head) == 1

    def unwrap_head(self):
        """
        Check that the head has only one item, and return it.
        """
        assert self.single_head()
        return self.head[0]


class Clauses(list):
    def single(self) -> bool:
        """
        Check that whether only one `Clause` exists in self.
        """
        return len(self) == 1


def match_clauses(node: ast.Subscript, raise_) -> Clauses:
    """
    Extract info from a `node` with lambdex compound statement syntax pattern.
    """

    # Clauses in `node` appears in an reversed order.
    #
    # e.g., `if_[][].else_[]`` has a structure
    # Subscript(
    #     slice=...,
    #     value=Attribute(
    #         attr='else_',
    #         value=Subscript(
    #             slice=...,
    #             value=Subscript(
    #                 slice=...,
    #                 value=Name('if_')
    #             )
    #         )
    #     )
    # )

    results = []
    body = head = name = None
    while node is not None:
        # If body is None, we are matching a new clause
        if isinstance(node, ast.Subscript) and body is None:
            body = value_from_subscript(node, force_list=True, raise_=raise_)
            node = node.value
            continue

        # Otherwise, the body has matched, we expect a head or a keyword

        # Match a head
        if isinstance(node, ast.Subscript) and head is None:
            head = value_from_subscript(node, force_list=True, raise_=raise_)
            node = node.value
            continue

        # Otherwise, the body and head are matched.  We expect a keyword.
        # The keyword may appear as a `Name` (first clause) or `Attribute` (sub-clause)

        # Match a sub-clause keyword
        if isinstance(node, ast.Attribute) and name is None:
            name = node.attr
            next_node = node.value

        # Match a first clause keyword
        if isinstance(node, ast.Name) and name is None:
            name = node.id
            next_node = None

        # If everything is OK, we construct and store a clause
        if name is not None:
            results.append(Clause(node, name, head, body))
            body = head = name = None
            node = next_node
            continue

        # Otherwise, return None as unmatched symbol
        return

    # Reverse the clauses so that they accord with definition order
    return Clauses(reversed(results))