import ast
import inspect
import astpretty

__all__ = [
    'pprint',
    'check',
    'value_from_subscript',
    'ast_from_source',
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
        if isinstance(ret, ast.Tuple):
            ret = ret.elts

        if not isinstance(ret, (tuple, list)):
            ret = [ret]

    return ret


def ast_from_source(source):
    if inspect.isfunction(source):
        source = inspect.getsource(source.__code__)
    return ast.parse(source).body[0]
