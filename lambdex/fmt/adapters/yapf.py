from typing import Sequence

import os

from lambdex.fmt.jobs_meta import JobsMeta
from lambdex.fmt.utils.io import _ResourceBase
from lambdex.fmt.utils.logger import getLogger
from lambdex.fmt.utils.importlib import silent_import

from ._base import BaseAdapter

logger = getLogger(__name__)


class YapfAdapter(BaseAdapter):
    def _make_jobs_meta(self) -> JobsMeta:
        _ParseArguments = silent_import('yapf', ['_ParseArguments', '_BuildParser'])
        file_resources = silent_import('yapf.yapflib.file_resources')

        bopts = self._backend_opts = _ParseArguments([' '] + self.backend_argv)

        if bopts.lines and len(bopts.files) > 1:
            logger.error('cannot use -l/--lines with more than one file')

        if (bopts.in_place or bopts.diff) and not bopts.files:
            logger.error('cannot use --in-place or --diff flags when reading from stdin')

        meta = JobsMeta(adapter='yapf')
        meta.in_place = bopts.in_place
        meta.parallel = bopts.parallel
        meta.print_diff = bopts.diff
        meta.quiet = bopts.quiet

        exclude_patterns_from_ignore_file = file_resources.GetExcludePatternsForDir(os.getcwd())
        files = file_resources.GetCommandLineFiles(
            bopts.files,
            bopts.recursive,
            (bopts.exclude or []) + exclude_patterns_from_ignore_file,
        )

        meta.files = files

        return meta

    def _get_backend_cmd_for_resource(self, resource: _ResourceBase) -> Sequence[str]:
        cmd = [self.opts.executable or 'yapf']

        bopts = self._backend_opts
        for linespec in bopts.lines or []:
            cmd.extend(['-l', linespec])
        if bopts.no_local_style:
            cmd.append('--no-local-style')
        if bopts.style is not None:
            cmd.extend(['--style', bopts.style])

        return cmd