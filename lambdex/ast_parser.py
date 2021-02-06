import ast
import typing
import inspect

from lambdex.utils.ast import ast_from_source
from lambdex.compiler import error

__all__ = ['lambda_to_ast']


def _shallow_match_ast(node, is_matched_fn):
    """
    Yields all children of `node` that fulfill `is_matched_fn` in a shallow manner.
    """
    if is_matched_fn(node):
        yield node
        return

    # Adapted from `ast.walk`
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    yield from _shallow_match_ast(item, is_matched_fn)
        elif isinstance(value, ast.AST):
            yield from _shallow_match_ast(value, is_matched_fn)


def _make_pattern(keyword: str, identifier: str):
    """
    Returns a function that matches a node of form `<keyword>.<identifier>(...)`
    or `<keyword>(...)` if `identifier` is empty.
    """
    def _pattern(node: ast.AST) -> bool:
        if node.__class__ is not ast.Call:
            return False

        declarer = node.func  # ast.Call

        # Use xx.__class__ is XX to improve efficiency
        if not identifier:
            return declarer.__class__ is ast.Name and keyword == declarer.id
        else:
            return (
                declarer.__class__ is ast.Attribute \
                and declarer.value.__class__ is ast.Name \
                and keyword == declarer.value.id \
                and identifier == declarer.attr
            )

    return _pattern


def lambda_to_ast(lambda_object: typing.Callable, *, keyword: str, identifier: str = ''):
    """
    Returns the AST of `lambda_object`.
    """
    tree = ast_from_source(lambda_object, keyword)
    if isinstance(tree, ast.Expr) and isinstance(tree.value, ast.Lambda):
        return tree.value

    pattern = _make_pattern(keyword, identifier)
    matched = list(_shallow_match_ast(tree, pattern))

    if not len(matched):
        raise SyntaxError('cannot parse lambda for unknown reason')

    if len(matched) > 1:
        decl = keyword if not identifier else keyword + '.' + identifier
        error.assert_(
            len(matched) == 1,
            'ambiguious declaration {!r}'.format(decl),
            matched[0],
            lambda_object.__code__.co_filename,
        )

    assert isinstance(matched[0], ast.Call)

    return matched[0]
