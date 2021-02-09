from typing import Sequence

import os
import argparse

from lambdex.fmt.jobs_meta import JobsMeta
from lambdex.fmt.utils.io import FileResource, StdinResource
from lambdex.fmt.utils.logger import getLogger
from lambdex.fmt.utils.importlib import silent_import
from lambdex.fmt.core.api import FormatCode

from ._base import BaseAdapter

logger = getLogger(__name__)


def _build_argument_parser():
    parser = argparse.ArgumentParser(description='Default formatter for lambdex')
    diff_inplace_quiet_group = parser.add_mutually_exclusive_group()
    diff_inplace_quiet_group.add_argument(
        '-d',
        '--diff',
        action='store_true',
        help='print the diff for the fixed source',
    )
    diff_inplace_quiet_group.add_argument(
        '-i',
        '--in-place',
        action='store_true',
        help='make changes to files in place',
    )
    diff_inplace_quiet_group.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='output nothing and set return value',
    )

    parser.add_argument(
        '-p',
        '--parallel',
        action='store_true',
        help='run in parallel when formatting multiple files.',
    )

    parser.add_argument('files', nargs='*', help='reads from stdin when no files are specified.')
    return parser


class DummyAdapter(BaseAdapter):
    def _make_jobs_meta(self) -> JobsMeta:
        parser = _build_argument_parser()

        bopts = parser.parse_args(self.backend_argv)

        if (bopts.in_place or bopts.diff) and not bopts.files:
            logger.error('cannot use --in-place or --diff flags when reading from stdin')

        meta = JobsMeta(adapter='yapf')
        meta.in_place = bopts.in_place
        meta.parallel = bopts.parallel
        meta.print_diff = bopts.diff
        meta.quiet = bopts.quiet
        meta.files = bopts.files

        return meta

    def _job(self, filename=None) -> bool:
        self._reset_aliases(filename)
        if filename is None:
            resource = StdinResource(self.jobs_meta)
        else:
            resource = FileResource(self.jobs_meta, filename)

        resource.set_backend_output(resource.source)

        formatted_code = FormatCode(resource.backend_output_stream.readline)
        resource.write_formatted_code(formatted_code)

        return resource.is_changed(formatted_code)

    def _get_backend_cmd_for_resource(self, resource) -> Sequence[str]:
        pass