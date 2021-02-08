"""
REPL patch for builtin Python REPL.

Since the builtin interactive loop is implemented in C and there is no
approach to hack the input, we decide to start a custom interactive
console that takes over the loop.
"""

import sys
import inspect
import linecache
import code as blcode
import __main__

_lines_cache = {}

from ... import keywords


class InteractiveConsole(blcode.InteractiveConsole):
    def __init__(self):
        locals = __main__.__dict__
        # Add keywords to globals dict
        # This ensures def_ is available after `from lambdex.repl import *`,
        # since the statements will never return
        locals.update({k: getattr(keywords, k) for k in keywords.__all__})

        super(InteractiveConsole, self).__init__(locals, '<lxshell#{}>')
        self._counter = 1

    def runsource(self, source, _):
        """
        Overwrite to cache input lines and setting filename.
        """
        filename = self.filename.format(self._counter)
        _lines_cache[filename] = source.splitlines()

        more = super(InteractiveConsole, self).runsource(source, filename)
        if not more:
            # The counter will not increase until the source is complete
            self._counter += 1

        return more

    def interact(self):
        """
        Overwrite to directly exit the process after interact() ends.
        """
        kwargs = dict(banner='')
        if sys.version_info > (3, 5, float('inf')):
            kwargs['exitmsg'] = ''
        super(InteractiveConsole, self).interact(**kwargs)
        sys.exit(0)


def _extended_linecache_getlines(
    filename,
    globals_dict=None,
    orig_getlines=linecache.getlines,  # Store the old function here
):
    """
    Patch `linecache.getlines` to obtain lines from `_lines_cache`.
    """
    if filename.startswith('<lxshell'):
        if filename in _lines_cache:
            return _lines_cache[filename]

    return orig_getlines(filename, globals_dict)


def _patch_sys_excepthook():
    """
    Patch `sys.excepthook`.

    If running with system-wide interpreter on Debian, `sys.excepthook`
    will be set to `apport_python_hook.apport_excepthook`, which removes
    traceback lines that aren't located in real file system. In this case,
    we reset `sys.excepthook`.
    """
    import sys
    try:
        import apport_python_hook
    except ImportError:
        return

    if sys.excepthook is apport_python_hook.apport_excepthook:
        sys.excepthook = sys.__excepthook__


def _start_console():
    """
    Start a custom interactive console, if haven't been started.
    """

    # Check stack frames to ensure that custom console not started
    for frameinfo in inspect.stack():
        if frameinfo.function != 'runsource': continue
        self = frameinfo.frame.f_locals.get('self', None)
        if isinstance(self, InteractiveConsole):
            return

    InteractiveConsole().interact()


def patch():
    """
    - Patch `linecache.getlines`.
    - Patch `sys.excepthook`.
    - Start a custom interactive console.
    """
    linecache.getlines = _extended_linecache_getlines
    _patch_sys_excepthook()
    _start_console()
