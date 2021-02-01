import sys
import argparse

from .. import adapters
from ..utils.logger import getLogger

logger = getLogger(__name__)

DELIMITTER = '--'


def split_argv():
    argv = sys.argv[1:]
    idx_delimitters = [i for i, arg in enumerate(argv) if arg == DELIMITTER]
    num_delimitters = len(idx_delimitters)
    if num_delimitters > 2:
        logger.error("Too many '--' found, expected less than 3")
        sys.exit(1)

    if num_delimitters == 0:
        return argv, ()
    elif num_delimitters == 1:
        idx = idx_delimitters[0]
        return argv[:idx], argv[idx + 1:]
    else:
        start, end = idx_delimitters
        return argv[:start] + argv[end + 1:], argv[start + 1:end]


def build_meta_parser():
    parser = argparse.ArgumentParser('Formatter for lambdex code')
    parser.add_argument('-a', '--adapter', default='yapf')
    parser.add_argument('-e', '--executable')
    return parser
