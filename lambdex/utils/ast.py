import ast
import astpretty

__all__ = [
    'pprint',
    'check',
    'value_from_subscript',
]


def pprint(ast_node):
    astpretty.pprint(ast_node, show_offsets=False)


def check(node, ast_type):
    assert isinstance(node, ast_type)


def value_from_subscript(node: ast.Subscript, *, force_list=False):
    slice_ = node.slice
    if isinstance(slice_, ast.Index):
        ret = slice_.value
    elif isinstance(slice_, ast.ExtSlice):
        ret = slice_.dims
    else:
        raise SyntaxError('Slice not allowed here.')

    if force_list:
        if not isinstance(ret, (tuple, list)):
            ret = [ret]

    return ret