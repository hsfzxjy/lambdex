"""
Manage the mapping between user-defined keywords/operators and internal
used symbols.
"""
import os
from keyword import iskeyword
from collections import namedtuple

from ._config import get_parser, ParsingError
from .utils.ops import COMPARATORS

_Aliases = namedtuple(
    '_Aliases',
    [
        'def_',
        'if_',
        'elif_',
        'else_',
        'for_',
        'while_',
        'with_',
        'try_',
        'except_',
        'finally_',
        'yield_',
        'yield_from_',
        'pass_',
        'return_',
        'from_',
        'raise_',
        'global_',
        'nonlocal_',
        'break_',
        'continue_',
        'callee_',

        # Coroutines related
        'async_def_',
        'async_with_',
        'async_for_',
        'await_',

        # From now on, the fields should start with captialized letters
        'Assignment',
        'As'
    ],
)

# Mapping between operator names and their string representations
_DEFAULT_OPS = {
    'Assignment': '<',
    'As': '>',
}

_aliases = None


def get_declarers():
    return {_aliases.def_, _aliases.async_def_}


def _validate_aliases(aliases: _Aliases):
    """
    Check that given `aliases` is valid.
    """
    for name, value in aliases._asdict().items():

        # If `name` is a keyword symbol
        if name[0].islower():
            # Ensure that it's an identifier
            if not value.isidentifier():
                raise ParsingError('alias for {!r} should be an identifier, got {!r}'.format(name, value))
            # Ensure that it's not a keyword
            if iskeyword(value):
                raise ParsingError('alias for {!r} should not be a keyowrd, got {!r}'.format(name, value))

        # If `name` is an operator symbol
        else:
            # Ensure that it's a valid comparator
            if value not in COMPARATORS:
                raise ParsingError('alias for {!r} should be one of {}, got {!r}'.format(
                    name, ' '.join(map(repr, COMPARATORS)), value
                ))


def get_aliases(userpaths=(), reinit=False) -> _Aliases:
    """
    Return or rebuild an _Aliases instance.

    `userpaths` and `reinit` are for building the config parser.
    """
    global _aliases
    if _aliases is not None and not reinit: return _aliases

    # Initialize the default building arguments
    build_kwargs = {}
    for name in _Aliases._fields:
        if name[0].islower():
            build_kwargs[name] = name
        else:
            build_kwargs[name] = _DEFAULT_OPS[name]

    if os.getenv('LXALIAS') is not None:
        parser = get_parser(userpaths, reinit=reinit)
        if parser.has_section('aliases'):
            for name in build_kwargs:
                if name in parser['aliases']:
                    build_kwargs[name] = parser['aliases'][name]

    _aliases = _Aliases(**build_kwargs)
    _validate_aliases(_aliases)

    return _aliases
