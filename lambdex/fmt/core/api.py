from typing import Optional

from ..config import Config
from ..utils.result import Result
from .tkutils.tokenize import tokenize
from .transforms import transform, AsCode
from ..utils.io import FileResource


def format_files(config: Config, result: Result):
    filenames = config.files or [None]
    for filename in filenames:
        format_file(config, result, filename)


def format_file(config: Config, result: Result, filename: Optional[str] = None):
    file_resource = FileResource(config, result, filename)
    fd = file_resource.open()

    seq = tokenize(fd.__next__)
    output = AsCode(transform(seq))

    file_resource.write(output)
