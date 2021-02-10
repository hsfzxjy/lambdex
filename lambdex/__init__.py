import os
import sys


def _is_run_as_script():
    """
    Check that whether lambdex is run as top-level script.

    We iterate from the stack bottom to find the first frame that contains
    no 'importlib' string, which should be the importer of lambdex.

    If the importer has any system prefixes, we assert that lambdex is run
    as top-level script.
    """
    from os.path import dirname
    from .utils.sysinfo import get_importer_path, get_site_paths

    importer_path = get_importer_path()

    if not importer_path:
        return False

    for sitepath in get_site_paths():
        prefix = dirname(dirname(dirname(sitepath)))  # such as '/usr/local'
        if importer_path.startswith(prefix):
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

del os, sys, _is_run_as_script

__version__ = "0.5.0"
