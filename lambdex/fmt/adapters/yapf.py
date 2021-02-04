import os

from ._bases import BaseAdapter
from ..config import Config


def silent_import(dotted_name: str, names: typing.Optional[typing.Sequence[str]] = None) -> typing.Optional[typing.Any]:
    try:
        mod = importlib.import_module(dotted_name)
    except ModuleNotFoundError:
        return None

    if names is None:
        return mod

    for name in names:
        if hasattr(mod, name):
            return getattr(mod, name)

    return None


_ParseArguments = silent_import('yapf', ['_ParseArguments', '_BuildParser'])
file_resources = silent_import('yapf.yapflib.file_resources')


class YapfAdapter(BaseAdapter):
    def _make_config(self) -> Config:
        args = _ParseArguments([' '] + self.extra_args)
        cfg = Config(adapter='yapf')
        cfg.inplace = args.in_place
        cfg.parallel = args.parallel
        cfg.print_diff = args.diff

        if cfg.print_diff:
            self.extra_args = [x for x in self.extra_args if x not in ('-d', '--diff')]

        exclude_patterns_from_ignore_file = file_resources.GetExcludePatternsForDir(os.getcwd())
        files = file_resources.GetCommandLineFiles(
            args.files,
            args.recursive,
            (args.exclude or []) + exclude_patterns_from_ignore_file,
        )

        cfg.files = files

        return cfg
