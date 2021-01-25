import sys
import abc
import argparse
import subprocess
from typing import Sequence
from dataclasses import dataclass

from ..config import Config
from ..utils.result import Result


class BaseAdapter(abc.ABC):
    def __init__(self, parsed_opts: argparse.Namespace, extra_args: Sequence[str]):
        self.parsed_opts = parsed_opts
        self.extra_args = extra_args

        self.config = self._make_config()

    @abc.abstractmethod
    def _make_config(self) -> Config:
        pass

    def run(self) -> Result:
        stdout = subprocess.PIPE if not self.config.inplace else None
        process = subprocess.Popen(
            [self.parsed_opts.executable or self.parsed_opts.adapter] + self.extra_args,
            stdout=stdout,
        )
        output, _ = process.communicate()

        if self.config.inplace:
            output = None
        else:
            output = output.decode()

        return Result(
            success=process.returncode == 0,
            output=output,
        )
