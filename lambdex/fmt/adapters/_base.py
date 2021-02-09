import abc
import argparse
import subprocess
from functools import partial
from typing import Sequence

from lambdex.fmt.jobs_meta import JobsMeta
from lambdex.fmt.core.api import FormatCode
from lambdex.fmt.utils.logger import getLogger
from lambdex.fmt.utils.io import StdinResource, FileResource, _ResourceBase

logger = getLogger(__name__)


class Result:

    __slots__ = ['success', 'output']

    def __init__(self, success: bool, output: bytes):
        self.success = success
        self.output = output


class BaseAdapter(abc.ABC):
    def __init__(self, opts: argparse.Namespace, backend_argv: Sequence[str]):
        self.opts = opts
        self.backend_argv = backend_argv

        self.jobs_meta = self._make_jobs_meta()

    @abc.abstractmethod
    def _make_jobs_meta(self) -> JobsMeta:
        pass

    @abc.abstractmethod
    def _get_backend_cmd_for_resource(self, resource: _ResourceBase) -> Sequence[str]:
        pass

    def _reset_aliases(self, filename):
        from lambdex.fmt.core.tkutils.rules import matcher

        if filename is None:
            matcher.reset_aliases()
        else:
            matcher.reset_aliases(filename)

    def _job(self, filename=None) -> bool:
        self._reset_aliases(filename)
        if filename is None:
            resource = StdinResource(self.jobs_meta)
        else:
            resource = FileResource(self.jobs_meta, filename)

        cmd = self._get_backend_cmd_for_resource(resource)
        backend_result = self.call_backend(cmd, resource.source)
        if not backend_result.success:
            logger.error('backend exits unexpectedly')
        resource.set_backend_output(backend_result.output)

        formatted_code = FormatCode(resource.backend_output_stream.readline)
        resource.write_formatted_code(formatted_code)

        return resource.is_changed(formatted_code)

    def get_jobs(self):
        if not self.jobs_meta.files:
            yield self._job
        else:
            yield from (partial(self._job, filename) for filename in self.jobs_meta.files)

    def call_backend(self, cmd: Sequence[str], stdin: bytes) -> Result:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        output, _ = process.communicate(input=stdin)
        return Result(
            success=process.returncode == 0,
            output=output,
        )
