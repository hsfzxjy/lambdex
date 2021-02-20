from typing import Tuple, Dict, Optional, Union

import ast
import types
import inspect
import textwrap
import linecache
from itertools import chain

from lambdex.utils.ast import ast_from_source
from lambdex.compiler import error

from lambdex._aliases import get_aliases, get_declarers

__all__ = ['lambda_to_ast', 'find_lambdex_ast_in_code', 'LambdexASTLookupKey', 'LambdexASTLookupTable']


def _shallow_match_ast(node, match, *, yield_node_only=True):
    """
    Yields all children of `node` that fulfill `match` in a shallow manner.
    """

    match_result = match(node)
    if match_result is not None:
        yield (node if yield_node_only else (node, match_result))
        lambda_args = node.args[0].args
        children = enumerate(chain(lambda_args.kw_defaults, lambda_args.defaults))
    else:
        children = ast.iter_fields(node)

    # Adapted from `ast.walk`
    for _, value in children:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    yield from _shallow_match_ast(item, match, yield_node_only=yield_node_only)
        elif isinstance(value, ast.AST):
            yield from _shallow_match_ast(value, match, yield_node_only=yield_node_only)


def _make_pattern(keyword: str, identifier: str):
    """
    Returns a function that matches a node of form `<keyword>.<identifier>(...)`
    or `<keyword>(...)` if `identifier` is empty.
    """

    if keyword is None:
        assert identifier is None
        get_aliases()
        declarers = get_declarers()

        def _match(node):
            if node.__class__ is ast.Name and node.id in declarers:
                return (node.id, None)
            elif node.__class__ is ast.Attribute and node.value.__class__ is ast.Name and node.value.id in declarers:
                return (node.value.id, node.attr)
            else:
                return None
    elif not identifier:

        def _match(node):
            if node.__class__ is ast.Name and keyword == node.id:
                return (keyword, None)
            return None
    else:

        def _match(node):
            if (node.__class__ is ast.Attribute and node.value.__class__ is ast.Name and keyword == node.value.id
                    and identifier == node.attr):
                return (keyword, identifier)

            return None

    def _pattern(node: ast.AST) -> bool:
        if node.__class__ is not ast.Call or len(node.args) != 1 or node.args[0].__class__ != ast.Lambda:
            return None

        return _match(node.func)

    return _pattern


def _raise_ambiguity(node, filename, keyword, identifier):
    """
    Raise SyntaxError reporting an ambiguious declaration.
    """
    decl = keyword if not identifier else keyword + '.' + identifier
    error.assert_(False, 'ambiguious declaration {!r}'.format(decl), node, filename)


def lambda_to_ast(lambda_object: types.FunctionType, *, keyword: str, identifier: str = ''):
    """
    Returns the AST of `lambda_object`.
    """
    tree = ast_from_source(lambda_object, keyword)
    if isinstance(tree, ast.Expr):
        assert not isinstance(tree.value, ast.Lambda)

    pattern = _make_pattern(keyword, identifier)
    matched = list(_shallow_match_ast(tree, pattern))

    if not len(matched):
        raise SyntaxError('cannot parse lambda for unknown reason')

    if len(matched) > 1:
        _raise_ambiguity(matched[0], lambda_object.__code__.co_filename, keyword, identifier)

    assert isinstance(matched[0], ast.Call)

    return matched[0]


LambdexASTLookupKey = Tuple[int, str, Optional[str]]
LambdexASTLookupTable = Dict[LambdexASTLookupKey, ast.AST]


def find_lambdex_ast_in_code(code: types.CodeType, ismod: bool) -> LambdexASTLookupTable:
    """
    Find out all possible lambdex declaration AST nodes within the source of `code`.
    """
    if ismod:
        lines = linecache.getlines(code.co_filename)
    else:
        lines, lnum = inspect.getsourcelines(code)
        lines = ['\n'] * (lnum - 1) + lines
    lines = textwrap.dedent(''.join(lines))
    ast_node = ast.parse(lines)
    table = {}
    iterator = _shallow_match_ast(ast_node, _make_pattern(None, None), yield_node_only=False)
    for lambdex_node, (keyword, identifier) in iterator:
        key = (lambdex_node.lineno, keyword, identifier)
        if key in table:
            _raise_ambiguity(lambdex_node, code.co_filename, keyword, identifier)

        table[key] = lambdex_node

    return table
