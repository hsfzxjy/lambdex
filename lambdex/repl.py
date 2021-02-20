from .utils.repl_compat import patch

# Export all keywords
from ._exports import *
from ._exports import __all__

# Patch the current REPL environment
patch()