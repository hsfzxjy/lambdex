import ast
import inspect
import textwrap

from .ops import COMPARATORS_S2A

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
    'cast_to_ctx',
    'check_compare',
    'check_as',
    'is_coroutine_ast',
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


def value_from_subscript(node: ast.Subscript, *, force_list=False, raise_=None):
    """
    Extract value(s) from the brackets of `node`.

    If `force_list` is `True`, result will be guaranteed as a list.
    Otherwise the original value will be returned.
    """
    def _raise_slice_error():
        message = "':' is not allowed in '[]'"
        if callable(raise_):
            raise_(message, node.value)
        else:
            raise SyntaxError(message)

    slice_ = node.slice
    if isinstance(slice_, ast.Index):
        ret = slice_.value
    elif isinstance(slice_, ast.ExtSlice):
        for dim in slice_.dims:
            if isinstance(dim, ast.Slice):
                _raise_slice_error()
        ret = slice_.dims
    elif isinstance(slice_, ast.Tuple):
        for elt in slice_.elts:
            if isinstance(elt, ast.Slice):
                _raise_slice_error()
        ret = slice_
    elif not isinstance(slice_, ast.Slice):
        ret = slice_
    else:
        _raise_slice_error()

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

        # Append line-ending if necessary
        for idx in range(len(lines)):
            if not lines[idx].endswith('\n'):
                lines[idx] += '\n'

        # Lines starting from `lnum` may contain enclosing tokens of previous expression
        # We use `keyword` to locate the true start point of source
        while True:
            first_keyword_loc = lines[lnum].find(keyword)
            if first_keyword_loc >= 0: break
            lnum -= 1

        lines = [lines[lnum][first_keyword_loc:]] + lines[lnum + 1:]
        # Prepend the lines with newlines, so that parsed AST will have correct lineno
        source_lines = ['\n'] * lnum + inspect.getblock(lines)
        source = ''.join(source_lines)

    # Some garbage may still remain at the end, we alternatively try compiling
    # and popping the last character until the source is valid.
    exc = None
    original_source = source
    while source:
        try:
            return ast.parse(source).body[0]
        except SyntaxError as e:
            source = source[:-1]
            exc = e
    else:
        # This should never happen
        raise RuntimeError('cannot parse the snippet into AST:\n{}'.format(original_source)) from exc


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


def cast_to_ctx(node: ast.AST, ctx=ast.Store()):
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
        n.ctx = ctx
        if isinstance(n, (ast.List, ast.Tuple, ast.Starred)):
            todo.extend(ast.iter_child_nodes(n))

    return node


def _expected_syntax_repr(type_, num):
    assert type_ in COMPARATORS_S2A
    op = COMPARATORS_S2A[type_]

    if num is None:
        return '... {op} ... [{op} ...]'.format(op=op)
    else:
        return ' {op} '.format(op=op).join(['...'] * num)


def check_compare(ctx, node: ast.Compare, expected_type, expected_num=None):
    """
    Check that `node.ops` are all with type `expected_type`.  If
    `expected_num` given, also check that `node` has `expected_num`
    operands.

    Return a tuple of all operands of `node`.
    """
    syntax_repr = _expected_syntax_repr(expected_type, expected_num)
    op_repr = COMPARATORS_S2A[expected_type]
    ctx.assert_is_instance(node, ast.Compare, 'expect {!r}'.format(syntax_repr))

    for idx, op in enumerate(node.ops):
        ctx.assert_(
            isinstance(op, expected_type),
            'expect {!r} before'.format(op_repr),
            node.comparators[idx],
        )

    if expected_num is not None:
        assert expected_num == 2
        ctx.assert_(
            expected_num == len(node.ops) + 1,
            'too many operands',
            lambda: node.comparators[expected_num - 1],
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
        return lhs, cast_to_ctx(rhs)


def is_coroutine_ast(x):
    """
    Check if `x` is coroutine AST node or AST type. 
    """
    if isinstance(x, ast.AST): x = type(x)
    return x in (ast.AsyncFunctionDef, ast.AsyncWith, ast.AsyncFor, ast.Await)


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
