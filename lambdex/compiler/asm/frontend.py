import os
import re
import sys
import types
import linecache
import importlib
import threading
import traceback

if sys.version_info > (3, 6, float('inf')):
    from queue import SimpleQueue
    from py_compile import PycInvalidationMode
else:
    import enum
    from queue import Queue as SimpleQueue

    class PycInvalidationMode(enum.Enum):
        TIMESTAMP = 1
        CHECKED_HASH = 2
        UNCHECKED_HASH = 3


if sys.version_info < (3, 7, 2):

    def _get_default_invalidation_mode():
        if os.environ.get('SOURCE_DATE_EPOCH'):
            return PycInvalidationMode.CHECKED_HASH
        else:
            return PycInvalidationMode.TIMESTAMP
else:
    from py_compile import _get_default_invalidation_mode

RE_LAMBDEX_REWRITE = re.compile(rb'#\s*lambdex:\s*modopt')


def _transpile_file(file, optimize=-1, invalidation_mode=None):
    """
    Given a source filename, try to transpile the bytecodes and write to corresponding
    .pyc file.

    Adapted from py_compile.py.
    """
    if invalidation_mode is None:
        invalidation_mode = _get_default_invalidation_mode()

    if optimize >= 0:
        optimization = optimize if optimize >= 1 else ''
        cfile = importlib.util.cache_from_source(file, optimization=optimization)
    else:
        cfile = importlib.util.cache_from_source(file)

    if os.path.islink(cfile):
        msg = ('{} is a symlink and will be changed into a regular file if ' 'import writes a byte-compiled file to it')
        raise FileExistsError(msg.format(cfile))
    elif os.path.exists(cfile) and not os.path.isfile(cfile):
        msg = (
            '{} is a non-regular file and will be changed into a regular '
            'one if import writes a byte-compiled file to it'
        )
        raise FileExistsError(msg.format(cfile))

    loader = importlib.machinery.SourceFileLoader('<py_compile>', file)
    lines = linecache.getlines(file)
    if lines:
        source_bytes = ''.join(lines).encode('utf-8')
    else:
        source_bytes = loader.get_data(file)
    if RE_LAMBDEX_REWRITE.search(source_bytes) is None:
        return None

    code = loader.source_to_code(source_bytes, file, _optimize=optimize)
    from lambdex.compiler.asm.core import transpile
    code = transpile(code, ismod=True)

    try:
        dirname = os.path.dirname(cfile)
        if dirname:
            os.makedirs(dirname)
    except FileExistsError:
        pass
    if invalidation_mode == PycInvalidationMode.TIMESTAMP:
        source_stats = loader.path_stats(file)
        if sys.version_info < (3, 6, float('inf')):
            serialize = importlib._bootstrap_external._code_to_bytecode
        else:
            serialize = importlib._bootstrap_external._code_to_timestamp_pyc

        bytecode = serialize(code, source_stats['mtime'], source_stats['size'])
    else:
        source_hash = importlib.util.source_hash(source_bytes)
        bytecode = importlib._bootstrap_external._code_to_hash_pyc(
            code,
            source_hash,
            (invalidation_mode == PycInvalidationMode.CHECKED_HASH),
        )
    mode = importlib._bootstrap_external._calc_mode(file)
    importlib._bootstrap_external._write_atomic(cfile, bytecode, mode)
    return cfile


# We do the module bytecodes transpilation in another thread, so that it will
# not block the main thread. This thread is looping forever and not daemonic.
#
# To ensure that the transpilation thread would gracefully exit when the program
# ends, we start another monitor thread, which is daemonic and will send a
# signal to the former one after the main thread ends.
# (Reference: https://stackoverflow.com/questions/58910372/)
_job_thread = _monitor_thread = None
_job_history = set()
_job_queue = SimpleQueue()
_done_queue = None


def _transpilation_target():
    """
    Transpilation thread.
    """
    while True:
        file = _job_queue.get()  # blocking

        if file is None:  # exit sentinel
            return

        if file in _job_history:  # skip if handled
            continue

        _job_history.add(file)
        if file[0] == '<' and file[-1] == '>':  # skip if not a file
            continue

        try:
            _transpile_file(file)
            if _done_queue is not None:
                _done_queue.put((file, 'ok'))
        except Exception as exc:
            # fail silently
            if os.getenv('LXBC_DEBUG') is not None:
                traceback.print_exception(*sys.exc_info())
            if _done_queue is not None:
                _done_queue.put((file, 'fail'))


def _monitor_target():
    """
    Monitor thread.

    Block until main thread exits, then signal the transpilation thread with None.
    """
    main_thread = threading.main_thread()
    main_thread.join()
    _job_queue.put(None)


# We only do bytecode transpilation for Python 3.6+
if sys.version_info < (3, 5, float('inf')):

    def transpile_file(modname: str):
        """
        Not available in Python 3.5 or below.
        """
        pass

    def asmopt(func):
        """
        Not available in Python 3.5 or below.
        """
        return func
else:

    def transpile_file(modname: str):
        """
        Asynchronously transpile the .pyc file of module `modname`.
        """
        global _job_thread, _monitor_thread

        mod = sys.modules.get(modname)
        if not hasattr(mod, '__file__'):
            return

        _job_queue.put(mod.__file__)
        if _job_thread is None:
            if _monitor_thread is None:
                _monitor_thread = threading.Thread(target=_monitor_target, daemon=True)
            _monitor_thread.start()
            _job_thread = threading.Thread(target=_transpilation_target, daemon=False)
            _job_thread.start()

    def asmopt(func: types.FunctionType) -> types.FunctionType:
        """
        Optimize the bytecodes of `func` by eliminating runtime lambdex transpilation.
        """
        from lambdex.compiler.asm.core import transpile
        code = transpile(func.__code__, ismod=False)
        new_func = types.FunctionType(
            code,
            func.__globals__,
            func.__name__,
            func.__defaults__,
            func.__closure__,
        )
        new_func.__annotations__ = func.__annotations__
        return new_func
