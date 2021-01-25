import sys
import pathlib
from typing import Optional
from ..config import Config
from .result import Result

import difflib


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
        self._original_content = None

    def read(self) -> str:
        if self.config.from_stdin:
            return self.result.output

        self._original_content = pathlib.Path(self.filename).read_text()
        return self._original_content

    def write(self, output: str):
        content = output
        if self.config.print_diff:
            before = self._original_content.splitlines()
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