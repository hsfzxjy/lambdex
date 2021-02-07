import os
import sys

colorful = os.getenv('NOCOLOR') is None
if colorful:
    try:
        from termcolor import colored
    except ImportError:
        colorful = False

if not colorful:
    colored = lambda msg, *_, **__: msg
