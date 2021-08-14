import typing

from ._base import BaseAdapter
from .yapf import YapfAdapter
from .dummy import DummyAdapter
from .black import BlackAdapter

mapping = {
    "yapf": YapfAdapter,
    "dummy": DummyAdapter,
    "black": BlackAdapter,
}


def build(name: str, *args) -> BaseAdapter:
    return mapping[name](*args)
