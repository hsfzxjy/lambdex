"""
REPL patch for Python IDLE.

IDLE separate code execution backend from the frontend, and source lines are
stored in frontend. The backend and frontend communicates with RPC. If we have
access to the RPC handler, we can invoke `linecache.getlines(...)` in frontend.

The patch is in two parts:
    1) We search for the RPC handler by iterating the stack;
    2) Hack `linecache.getlines` (the one in backend) to obtain source lines
       from frontend, if necessary.
"""
import sys
import linecache
import idlelib.run

_rpchandler = None
_local_lines_cache = {}


def get_rpchandler():
    """
    Obtain the RPC handler.

    The handler should be accessible in the frame `idlelib.run.Executive::runcode`,
    and be the member `self.rpchandler`.
    """
    global _rpchandler
    if _rpchandler is not None:
        return _rpchandler

    frame = sys._getframe(1)
    while frame is not None and frame.f_code is not None:
        f_code = frame.f_code
        is_runcode = frame.f_code.co_name == 'runcode'
        self = frame.f_locals.get('self')
        is_Executive = isinstance(self, idlelib.run.Executive)

        if is_runcode and is_Executive:
            break

        frame = frame.f_back
    else:
        raise RuntimeError('cannot find TCP handler of IDLE')

    _rpchandler = self.rpchandler
    return _rpchandler


def _extended_linecache_getlines(
    filename,
    globals_dict=None,
    orig_getlines=linecache.getlines,
):
    """
    Patch `linecache.getlines` to obtain lines from remote.
    """

    # If found in local cache, simply return it
    if filename in _local_lines_cache:
        return _local_lines_cache[filename]

    # If is source lines entered in IDLE, invoke a remote call
    if filename.startswith('<pyshell'):
        handler = get_rpchandler()
        lines = handler.remotecall('linecache', 'getlines', (filename, globals_dict), {})
        _local_lines_cache[filename] = lines
        return lines

    # Otherwise, call the original function
    return orig_getlines(filename, globals_dict)


def patch():
    """
    - Patch `linecache.getlines`.
    """
    linecache.getlines = _extended_linecache_getlines
