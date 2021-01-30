from typing import Optional

import libcst

from ..config import Config
from ..utils.result import Result
from ..utils.io import FileResource

from .transform import MainTransformer


def format_file(config: Config, result: Result, filename: Optional[str] = None):
    file_resource = FileResource(config, result, filename)
    string = file_resource.read()

    if 'def_' not in string:
        output = string
    else:
        tree = libcst.parse_module(string)
        transformer = MainTransformer()
        tree = tree.visit(transformer)
        output  = tree.code

    file_resource.write(output)


def format_files(config: Config, result: Result):
    filenames = config.files or [None]
    for filename in filenames:
        format_file(config, result, filename)