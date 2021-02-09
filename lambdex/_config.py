"""
Define the config parser for universal lambdex configuration, e.g., keyword
aliases or styles.
"""

from typing import List, Optional

import os
import pathlib
import configparser

from .utils.sysinfo import get_importer_path


def _is_readable_file(path):
    """
    Check if a given path is a file and is readable.
    """
    path = str(path)
    return os.access(path, os.R_OK) and os.path.isfile(path)


def _walk_parents(paths: List[pathlib.Path]):
    """
    A genrator that yields all parents of path in `paths`. Each path yielded
    will appear only once.
    """
    visited = set()
    for path in paths:
        path = pathlib.Path(path).absolute()

        # If path is a file, walk upwards
        if _is_readable_file(path):
            path = path.parent

        # Walk upwards until reach the root
        while True:
            # If a path is visited, all of its parents should also be
            if path in visited: break

            visited.add(path)
            yield path

            # If reach the root, try another path
            if path.parent == path: break

            path = path.parent


def _find_config_file(userpaths: List[str], filename='.lambdex.cfg') -> Optional[pathlib.Path]:
    """
    Search for the first file with filename `filename` in the order below:

    - Path of the direct importer (if any);
    - Paths in `userpaths`;
    - CWD.

    For each path, we try all of its parents until reach the root.

    If envvar LXNOCFG set, simply return None (don't use any config files).
    """
    if os.getenv('LXNOCFG') is not None:
        return None

    paths = []

    # Append importer path if available.
    importer_path = get_importer_path()
    if importer_path is not None:
        paths.append(importer_path)

    # Append userpaths
    paths.extend(userpaths)

    # Apeend CWD
    paths.append(os.getcwd())

    for path in _walk_parents(paths):
        cfg_file = path / filename
        # Check if the file exists and is readable
        if _is_readable_file(cfg_file):
            return cfg_file

    return None


_parser = None
_config_path = None


def get_parser(userpaths: List[str], reinit=False) -> configparser.ConfigParser:
    """
    Build and return a config parser.

    `userpaths` is for searching config file.  If a config file found, the parser
    will read from it.

    If `reinit` is True, the function will always try to build a new parser;
    otherwise the parser will be cached.
    """
    global _parser, _config_path
    if _parser is None or reinit:
        _config_path = _find_config_file(userpaths)
        _parser = configparser.ConfigParser()
        if _config_path is not None:
            with _config_path.open('r', encoding='utf-8') as fd:
                _parser.read_file(fd)

    return _parser


def get_config_path() -> Optional[pathlib.Path]:
    """
    Return the config file path that current parser reads from.
    """
    return _config_path


ParsingError = configparser.ParsingError