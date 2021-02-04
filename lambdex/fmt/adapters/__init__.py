import typing
from typing import Mapping

from ._base import BaseAdapter
from .yapf import YapfAdapter
from .dummy import DummyAdapter

mapping: Mapping[str, BaseAdapter] = {
    'yapf': YapfAdapter,
    'dummy': DummyAdapter,
}


def build(name: str, *args) -> BaseAdapter:
    return mapping[name](*args)