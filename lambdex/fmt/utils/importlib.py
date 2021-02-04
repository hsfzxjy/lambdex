import typing
import importlib

from .logger import getLogger

logger = getLogger(__name__)


def silent_import(
    dotted_name: str,
    names: typing.Optional[typing.Sequence[str]] = None,
) -> typing.Optional[typing.Any]:
    try:
        mod = importlib.import_module(dotted_name)
    except ModuleNotFoundError:
        logger.warning('module {} not found'.format(dotted_name))
        return None

    if names is None:
        return mod

    for name in names:
        if hasattr(mod, name):
            return getattr(mod, name)

    logger.warning('attribute {} not found on module {}'.format(', '.join(names), dotted_name))
    return None
