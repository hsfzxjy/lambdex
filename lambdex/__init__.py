import os
import sys
import inspect

for f in inspect.stack()[1:]:
    if not f.filename.startswith('<'):
        break

if f.filename.startswith(os.path.dirname(os.__file__)):
    if sys.path and sys.path[0] == os.getcwd():
        sys.path = sys.path[1:]
else:
    __all__ = ['def_']
    from .keywords import def_

del os, sys, inspect, f

__version__ = "0.0.1"
