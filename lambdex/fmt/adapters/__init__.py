import typing
from typing import Mapping

from ._base import BaseAdapter
from .yapf import YapfAdapter

mapping: Mapping[str, BaseAdapter] = {
    'yapf': YapfAdapter,
}


def build(name: str, *args) -> BaseAdapter:
    return mapping[name](*args)