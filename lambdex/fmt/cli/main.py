import sys

from .opts import split_argv, build_meta_parser
from .. import adapters

from ..core.api import format_files


def main() -> int:
    adapter_argv, meta_argv = split_argv()
    meta_opts = build_meta_parser().parse_args(meta_argv)

    adapter = adapters.build(meta_opts.adapter, meta_opts, adapter_argv)

    config = adapter.config
    config.validate()

    result = adapter.run()

    if not result.success:
        return 1

    format_files(config, result)

    return 0
