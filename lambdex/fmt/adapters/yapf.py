from typing import Sequence

import os

from ..config import Config
from ..utils.io import _ResourceBase
from ..utils.logger import getLogger
from ..utils.importlib import silent_import

from ._base import BaseAdapter

logger = getLogger(__name__)


class YapfAdapter(BaseAdapter):
    def _make_config(self) -> Config:
        _ParseArguments = silent_import('yapf', ['_ParseArguments', '_BuildParser'])
        file_resources = silent_import('yapf.yapflib.file_resources')

        bopts = self._backend_opts = _ParseArguments([' '] + self.backend_argv)

        if bopts.lines and len(bopts.files) > 1:
            logger.error('cannot use -l/--lines with more than one file')

        if (bopts.in_place or bopts.diff) and not bopts.files:
            logger.error('cannot use --in-place or --diff flags when reading from stdin')

        cfg = Config(adapter='yapf')
        cfg.in_place = bopts.in_place
        cfg.parallel = bopts.parallel
        cfg.print_diff = bopts.diff
        cfg.quiet = bopts.quiet

        exclude_patterns_from_ignore_file = file_resources.GetExcludePatternsForDir(os.getcwd())
        files = file_resources.GetCommandLineFiles(
            bopts.files,
            bopts.recursive,
            (bopts.exclude or []) + exclude_patterns_from_ignore_file,
        )

        cfg.files = files

        return cfg

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