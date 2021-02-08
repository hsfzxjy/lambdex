from . import checks


def _noop():
    pass


if checks.is_idle:
    # Patch Python IDLE
    from .idle import patch
elif checks.is_ipython:
    # Check IPython before builtin, since `is_ipython is True` implies `is_builtin is True`

    # IPython requires no patching
    patch = _noop
elif checks.is_builtin:
    # Patch Python builtin REPL
    from .builtin import patch
else:
    # Otherwise, do nothing
    patch = _noop

del _noop
