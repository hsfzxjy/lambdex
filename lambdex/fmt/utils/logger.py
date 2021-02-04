import os
import sys
import logging

from .colored import colored

IS_DEBUG = os.getenv('DEBUG') is not None


class _Formatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = '{'
        kwargs.setdefault(
            'fmt',
            colored("[{funcName}] ", "green") + "{message}",
        )
        super(_Formatter, self).__init__(*args, **kwargs)

    def formatMessage(self, record):
        log = super(_Formatter, self).formatMessage(record)
        if record.levelno == logging.WARNING:
            prefix = colored("WARNING", "red", attrs=["blink"])
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            prefix = colored("ERROR", "red", attrs=["blink", "underline"])
        else:
            return log
        return prefix + " " + log


class _Logger(logging.Logger):
    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        orig_f = f
        while f and stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        if not f:
            f = orig_f
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == logging._srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()

            localvars = f.f_locals
            classname_prefix = ''
            if 'self' in localvars:
                classname_prefix = localvars['self'].__class__.__name__ + '::'

            rv = (co.co_filename, f.f_lineno, classname_prefix + co.co_name, sinfo)
            break
        return rv

    @property
    def is_debug(self):
        return IS_DEBUG

    def error(self, *args, **kwargs):
        super(_Logger, self).error(*args, **kwargs)
        sys.exit(2)


def getLogger(name: str) -> _Logger:
    logger = _Logger(name)

    formatter = _Formatter()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG if IS_DEBUG else logging.INFO)
    logger.addHandler(handler)

    return logger
