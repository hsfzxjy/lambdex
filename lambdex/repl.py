from .utils.repl_compat import patch

# Export all keywords
from .keywords import *
from .keywords import __all__

# Patch the current REPL environment
patch()