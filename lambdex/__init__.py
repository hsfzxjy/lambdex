import os
import sys

f = sys._getframe(1)
while f.f_code is not None and f.f_code.co_filename.startswith('<'):
    f = f.f_back

if f and f.f_code and f.f_code.co_filename.startswith(os.path.dirname(os.__file__)):
    if sys.path and sys.path[0] == os.getcwd():
        sys.path = sys.path[1:]
else:
    __all__ = ['def_']
    from .keywords import def_

del os, sys, f

__version__ = "0.1.0"
