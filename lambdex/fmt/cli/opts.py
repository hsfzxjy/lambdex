import sys
import argparse

from lambdex.fmt import adapters
from lambdex.fmt.utils.logger import getLogger

logger = getLogger(__name__)

DELIMITTER = '--'


def split_argv():
    argv = sys.argv[1:]
    idx_delimitters = [i for i, arg in enumerate(argv) if arg == DELIMITTER]
    num_delimitters = len(idx_delimitters)
    if num_delimitters > 2:
        logger.error("Too many '--' found, expected less than 3")

    if num_delimitters == 0:
        return argv, ()
    elif num_delimitters == 1:
        idx = idx_delimitters[0]
        return argv[:idx], argv[idx + 1:]
    else:
        start, end = idx_delimitters
        return argv[:start] + argv[end + 1:], argv[start + 1:end]


def build_parser():
    parser = argparse.ArgumentParser('lxfmt [ARGS OF BACKEND] --', description='Lambdex formatter as a post-processor for specific backend')
    parser.add_argument(
        '-b',
        '--backend',
        metavar='BACKEND',
        dest='adapter',
        default='dummy',
        choices=list(adapters.mapping),
        help='name of formatter backend (default: dummy)',
    )
    parser.add_argument(
        '-e',
        '--executable',
        help='executable of backend',
    )
    return parser
