import ast
import inspect
import textwrap

try:
    import astpretty
except ImportError:
    astpretty = None

__all__ = [
    'pprint',
    'pformat',
    'check',
    'value_from_subscript',
    'ast_from_source',
    'recursively_set_attr',
    'copy_lineinfo',
    'is_lvalue',
    'cast_to_lvalue',
    'check_compare',
    'check_as',
    'empty_arguments',
    'None_node',
]


def pprint(ast_node) -> None:
    """
    Pretty-print an AST node `ast_node`.
    """
    recursively_set_attr(ast_node, 'type_comment', '')
    astpretty.pprint(ast_node, show_offsets=False)


def pformat(ast_node) -> str:
    """
    Pretty-format an AST node `ast_node`, and return the string.
    """
    recursively_set_attr(ast_node, 'type_comment', '')
    return astpretty.pformat(ast_node, show_offsets=False)


def check(node, ast_type):
    """
    If `node` is not instance of `ast_type`, raise an error.
    """
    assert isinstance(node, ast_type)


def value_from_subscript(node: ast.Subscript, *, force_list=False):
    """
    Extract value(s) from the brackets of `node`.

    If `force_list` is `True`, result will be guaranteed as a list.
    Otherwise the original value will be returned.
    """
    slice_ = node.slice
    if isinstance(slice_, ast.Index):
        ret = slice_.value
    elif isinstance(slice_, ast.ExtSlice):
        ret = slice_.dims
    elif not isinstance(slice_, ast.Slice):
        ret = slice_
    else:
        raise SyntaxError('Slice not allowed here.')

    if force_list:
        if isinstance(ret, ast.Tuple):
            ret = ret.elts

        if not isinstance(ret, (tuple, list)):
            ret = [ret]

    return ret


def ast_from_source(source, keyword: str):
    """
    Return the AST representation of `source`.  `source` might be a function or
    string of source code.

    If `source` is a function, `keyword` is used to find the very start of its
    source code.
    """
    if inspect.isfunction(source):
        lines, lnum = inspect.findsource(source.__code__)

        # Lines starting from `lnum` may contain enclosing tokens of previous expression
        # We use `keyword` to locate the true start point of source
        while True:
            first_keyword_loc = lines[lnum].find(keyword)
            if first_keyword_loc >= 0: break
            lnum -= 1

        lines[lnum] = lines[lnum][first_keyword_loc:]
        # Prepend the lines with newlines, so that parsed AST will have correct lineno
        source = '\n' * lnum + ''.join(inspect.getblock(lines[lnum:]))

    return ast.parse(source).body[0]


def recursively_set_attr(node: ast.AST, attrname: str, value):
    """
    Recursively set attribute `attrname` to `value` on node and its children,
    if the field exists.
    """
    for n in ast.walk(node):
        if attrname in n._fields:
            setattr(n, attrname, value)

    return node


def copy_lineinfo(src: ast.AST, dst: ast.AST):
    """
    Copy metadata of lineno and column offset from `src` to `dst`.
    """
    for field in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset'):
        setattr(dst, field, getattr(src, field, None))

    return dst


def is_lvalue(node: ast.AST) -> bool:
    """
    Check whether `node` can be L-value.
    """
    from collections import deque
    todo = deque([node])
    while todo:
        n = todo.popleft()
        if 'ctx' not in n._fields:
            return False, n
        if isinstance(n, (ast.List, ast.Tuple, ast.Starred)):
            todo.extend(
                cn for cn in ast.iter_child_nodes(n) \
                if not isinstance(cn, ast.expr_context)
            )

    return True, None


def cast_to_lvalue(node: ast.AST):
    """
    Recursively set `ctx` to `Store()` on `node` and its children.  This
    function assumes that `is_lvalue()` check has passed.

    The behavior ony propagates down to children with type `ast.List`,
    `ast.Tuple` and `ast.Starred`. e.g. name `attr` in `a[attr]` will
    not be set.
    """
    from collections import deque
    todo = deque([node])
    while todo:
        n = todo.popleft()
        n.ctx = ast.Store()
        if isinstance(n, (ast.List, ast.Tuple, ast.Starred)):
            todo.extend(ast.iter_child_nodes(n))

    return node


def check_compare(ctx, node: ast.Compare, expected_type, expected_num=None):
    """
    Check that `node.ops` are all with type `expected_type`.  If
    `expected_num` given, also check that `node` has `expected_num`
    operands.

    Return a tuple of all operands of `node`.
    """
    op_name = repr(expected_type.__name__)
    for op in node.ops:
        ctx.assert_(isinstance(op, expected_type), 'expect ' + op_name, op)

    if expected_num is not None:
        ctx.assert_(
            expected_num == len(node.ops) + 1,
            'unexpected ' + op_name,
            lambda: node.ops[expected_num],
        )

    return (node.left, *node.comparators)


def check_as(ctx, node: ast.expr, as_op, *, rhs_is_identifier=False):
    """
    Check that `node` has pattern `lhs > rhs`.  Return `(lhs, rhs)`
    if matched, otherwise `(any, None)`.

    If `rhs_is_identifier` is `True`, `rhs` will be converted to L-value.
    """
    if not isinstance(node, ast.Compare):
        return node, None

    lhs, rhs = check_compare(ctx, node, as_op, 2)

    if rhs_is_identifier:
        ctx.assert_is_instance(rhs, ast.Name, 'expect identifier')
        return lhs, rhs.id
    else:
        ctx.assert_lvalue(rhs)
        return lhs, cast_to_lvalue(rhs)


empty_arguments = ast.arguments(
    posonlyargs=[],
    args=[],
    vararg=None,
    kwonlyargs=[],
    kw_defaults=[],
    kwarg=None,
    defaults=[],
)

None_node = ast.parse('None', '<consts>', mode='eval').body
