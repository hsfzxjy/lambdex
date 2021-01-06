import ast
import inspect
import astpretty

__all__ = [
    'pprint',
    'check',
    'value_from_subscript',
    'ast_from_source',
    'recursively_set_attr',
    'is_lvalue',
    'check_compare',
]


def pprint(ast_node):
    recursively_set_attr(ast_node, 'type_comment', '')
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


def recursively_set_attr(node: ast.AST, attrname: str, value):
    for n in ast.walk(node):
        if attrname in n._fields:
            setattr(n, attrname, value)

    return node


def is_lvalue(node: ast.AST):
    return hasattr(node, 'ctx')


def check_compare(node: ast.Compare, expected_type, expected_num=None):
    assert all(isinstance(n, expected_type) for n in node.ops)
    if expected_num is not None:
        assert expected_num == len(node.ops) + 1

    return (node.left, *node.comparators)
