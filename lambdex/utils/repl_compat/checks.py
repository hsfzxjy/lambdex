import sys
import __main__
import linecache

# If idlelib.run already imported, we recognize it as IDLE
is_idle = 'idlelib.run' in sys.modules

# IPython will set linecache._ipython_cache
is_ipython = hasattr(linecache, '_ipython_cache')

# If __main__ is non-file and (stdin is interactive or '-i' set)
is_builtin = (
    not hasattr(__main__, '__file__') \
    and (sys.stdin.isatty() or sys.flags.interactive)
)
