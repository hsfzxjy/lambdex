import typing

from .utils.logger import getLogger

logger = getLogger(__name__)


class Config:

    __slots__ = ['adapter', 'quiet', 'in_place', 'print_diff', 'parallel', 'files']

    def __init__(self, adapter: str):
        self.adapter = adapter
        self.quiet = False
        self.in_place = False
        self.print_diff = False
        self.parallel = False
        self.files = []

    @property
    def from_stdin(self):
        return not self.files
