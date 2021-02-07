import typing

from ._base import BaseAdapter
from .yapf import YapfAdapter
from .dummy import DummyAdapter

mapping = {
    'yapf': YapfAdapter,
    'dummy': DummyAdapter,
}


def build(name: str, *args) -> BaseAdapter:
    return mapping[name](*args)