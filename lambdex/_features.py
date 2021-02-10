"""
Manage the enability of language features.
"""
import os
from keyword import iskeyword
from collections import namedtuple

from ._config import get_parser, ParsingError

_Features = namedtuple(
    '_Features',
    [
        'await_attribute',
        'implicit_return',
    ],
)

_DEFAULT = _Features(
    await_attribute=False,
    implicit_return=False,
)

_features = None


def _parse_flag(flag: str):
    """
    Parse "y", "on" as True, and "n", "off" as False in a case-insensitive way.

    If invalid value encountered, return None.
    """
    flag = flag.lower()
    if flag in {'y', 'on'}: return True
    if flag in {'n', 'off'}: return False
    return None


def get_features(userpaths=(), reinit=False) -> _Features:
    """
    Return or rebuild an _Features instance.

    `userpaths` and `reinit` are for building the config parser.
    """
    global _features
    if _features is not None and not reinit: return _features

    _features = _DEFAULT
    build_kwargs = {}
    parser = get_parser(userpaths, reinit=reinit)
    if parser.has_section('features'):
        for name in _Features._fields:
            if name in parser['features']:
                flag = parser['features'][name]
                flag = _parse_flag(flag)
                if flag is None:
                    raise ParsingError("unknown option '{} = {}'".format(name, flag))
                build_kwargs[name] = flag

    _features = _features._replace(**build_kwargs)
    return _features
