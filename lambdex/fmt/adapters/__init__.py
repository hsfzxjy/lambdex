import typing
from typing import Dict

from ._bases import BaseAdapter
from .yapf import YapfAdapter

mapping: Dict[str, BaseAdapter] = {
    'yapf': YapfAdapter,
}


def build(name: str, *args) -> BaseAdapter:
    return mapping[name](*args)