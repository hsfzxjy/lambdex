import os
import sys


def _sitepaths():
    import site

    if hasattr(site, 'getsitepackages'):
        yield from site.getsitepackages()

    if hasattr(site, 'getusersitepackages'):
        yield site.getusersitepackages()


def _is_run_as_script():
    """
    Check that whether lambdex is run as top-level script.

    We iterate from the stack bottom to find the first frame that contains
    no 'importlib' string, which should be the importer of lambdex.

    If the importer has any system prefixes, we assert that lambdex is run
    as top-level script.
    """
    from os.path import dirname, abspath

    f = sys._getframe(1)
    while f is not None \
        and f.f_code is not None \
        and 'importlib' in f.f_code.co_filename:
        f = f.f_back

    if not (f or f.f_code):
        return False

    filename = abspath(f.f_code.co_filename)
    for sitepath in _sitepaths():
        prefix = dirname(dirname(dirname(sitepath)))  # such as '/usr/local'
        if filename.startswith(prefix):
            return True

    return False


# If run as top-level script, user is happened to use lxfmt.
# We remove CWD from sys.path, so that the files user editting will not
# cause name conflicts with built-in modules.
if _is_run_as_script():
    if sys.path and sys.path[0] == os.getcwd():
        sys.path = sys.path[1:]
# Otherwise, we import keywords as normal
else:
    from .keywords import *
    from .keywords import __all__

del os, sys, _sitepaths, _is_run_as_script

__version__ = "0.3.0"
