import sys

from .. import adapters
from .opts import split_argv, build_parser


def main() -> int:
    backend_argv, argv = split_argv()
    opts = build_parser().parse_args(argv)

    adapter = adapters.build(opts.adapter, opts, backend_argv)

    changed = False
    if adapter.config.parallel:
        import multiprocessing
        import concurrent.futures

        with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as executor:
            future_formats = [executor.submit(job) for job in adapter.get_jobs()]
            for future in concurrent.futures.as_completed(future_formats):
                changed |= future.result()
    else:
        for job in adapter.get_jobs():
            changed |= job()

    return 1 if changed and (adapter.config.print_diff or adapter.config.quiet) else 0
