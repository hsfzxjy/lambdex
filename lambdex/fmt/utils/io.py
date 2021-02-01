import sys
import pathlib
from typing import Optional
from ..config import Config
from .result import Result

import difflib
from io import BytesIO


class FileResource:
    def __init__(
        self,
        config: Config,
        result: Result,
        filename: Optional[str] = None,
    ):
        self.config = config
        self.result = result
        self.filename = filename
        self._buffer = BytesIO()

    def read_text(self) -> str:
        return self.open().read().decode()

    def open(self):
        if self.result.output is not None:
            self._buffer = BytesIO(self.result.output)
        else:
            with pathlib.Path(self.filename).open('rb') as fd:
                self._buffer = BytesIO(fd.read())

        return self._buffer

    def write(self, output: str):
        content = output
        if self.config.print_diff:
            self._buffer.seek(0)
            before = self._buffer.read().decode().splitlines()
            after = output.splitlines()
            content = '\n'.join(
                difflib.unified_diff(
                    before,
                    after,
                    'code',
                    'code',
                    '(original)',
                    '(reformatted)',
                    lineterm='',
                )
            ) + '\n'

        if self.config.inplace:
            pathlib.Path(self.filename).write_text(content)

        sys.stdout.write(content)