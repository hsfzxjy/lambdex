from typing import Sequence

import os
import sys
from collections import namedtuple
from contextlib import contextmanager

from lambdex.fmt.jobs_meta import JobsMeta
from lambdex.fmt.utils.io import _ResourceBase, StringResource
from lambdex.fmt.utils.logger import getLogger
from lambdex.fmt.utils.importlib import silent_import

from ._base import BaseAdapter

logger = getLogger(__name__)


StringSourceCode = namedtuple("StringSourceCode", "code")


@contextmanager
def _black_context(argv):
    black_main = silent_import("black", ["main"])
    click_Exit = silent_import("click.exceptions", ["Exit"])

    try:
        with black_main.make_context("black", argv) as ctx:
            yield ctx
    except click_Exit as exc:
        sys.exit(exc.exit_code)


class BlackAdapter(BaseAdapter):
    def _make_jobs_meta(self) -> JobsMeta:
        with _black_context(self.backend_argv) as ctx:
            return self._do_make_jobs_meta(ctx)

    def _do_make_jobs_meta(self, ctx) -> JobsMeta:
        black_get_sources = silent_import("black", ["get_sources"])

        bopts = self._backend_opts = ctx.params

        meta = JobsMeta(adapter="black")
        meta.print_diff = bopts["diff"]
        meta.quiet = False

        if bopts["code"] is not None:
            sources = [StringSourceCode(code=bopts["code"])]
        else:
            Report = silent_import("black.report", ["Report"])
            report = Report(
                check=bopts["check"],
                diff=bopts["diff"],
                quiet=bopts["quiet"],
                verbose=bopts["verbose"],
            )
            sources = black_get_sources(
                ctx=ctx,
                src=bopts["src"],
                quiet=bopts["quiet"],
                verbose=bopts["verbose"],
                include=bopts["include"],
                exclude=bopts["exclude"],
                extend_exclude=bopts["extend_exclude"],
                force_exclude=bopts["force_exclude"],
                report=report,
                stdin_filename=bopts["stdin_filename"],
            )
            sources = list(map(str, sources))

        meta.files = sources
        meta.parallel = len(sources) > 1
        meta.in_place = not meta.print_diff and not any(
            f == "-" or isinstance(f, StringSourceCode) for f in sources
        )

        return meta

    def _create_resource(self, filename) -> _ResourceBase:
        if isinstance(filename, StringSourceCode):
            return StringResource(self.jobs_meta, filename.code)

        return super()._create_resource(filename)

    def _get_backend_cmd_for_resource(self, resource: _ResourceBase) -> Sequence[str]:
        cmd = [self.opts.executable or "black", "-", "-q"]
        bopts = self._backend_opts

        if bopts["config"] is not None:
            cmd.extend(["--config", bopts["config"]])

        cmd.extend(["--line-length", str(bopts["line_length"])])

        if bopts["skip_magic_trailing_comma"]:
            cmd.append("--skip-magic-trailing-comma")

        if bopts["skip_string_normalization"]:
            cmd.append("--skip-string-normalization")

        return cmd

        # for linespec in bopts.lines or []:
        #     cmd.extend(["-l", linespec])
        # if bopts.no_local_style:
        #     cmd.append("--no-local-style")
        # if bopts.style is not None:
        #     cmd.extend(["--style", bopts.style])

        # return cmd
